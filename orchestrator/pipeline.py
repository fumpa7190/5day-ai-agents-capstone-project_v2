"""Runs the lesson-prep workflow as three discrete, teacher-paced stages that
each build on everything generated before them:

  1. Curriculum Matching (deterministic) -> Lesson Planning (LLM, skill-equipped)
  2. Activities -> Teacher Notes (LLM, sequential, skill-equipped), given the Lesson Plan
  3. Assessment (LLM, skill-equipped), given the Lesson Plan *and* the Activities/Teacher Notes

Each stage is its own function so the frontend can show a stage's result and
let the teacher decide to continue, rather than generating everything blind in
one call. State carries forward explicitly (the matched curriculum record, the
raw text of every prior stage) - stages 2 and 3 never re-run Curriculum
Matching or Lesson Planning, and stage 3 never re-runs stage 2.

Each LLM agent below carries its own scoped SkillToolset (built in agents/*.py)
- the procedural "how to write this" knowledge lives in skills/*/SKILL.md, not
in this orchestrator or in the agent prompts. See specs/png-classroom-agent-workflow.md
for the workflow this implements.
"""

import json
import logging
from typing import Optional

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents._shared import get_local_model
from agents.activities import build_activities_agent
from agents.assessment import build_assessment_agent
from agents.lesson_planning import build_lesson_planning_agent
from agents.teacher_notes import build_teacher_notes_agent
from schemas.curriculum import ClassroomContext, CurriculumMatch, TeacherSelection
from schemas.sections import ActivitiesSections, AssessmentSections, LessonPlanSections, TeacherNotesSections
from services.content_safety import check_topic_safety
from services.curriculum_store import get_store
from services.markdown_sections import parse as parse_markdown
from services.markdown_sections import sanitize_dollar_signs

logger = logging.getLogger("orchestrator.pipeline")

USER_ID = "local_teacher"


async def _run_agents(agents: list[LlmAgent], initial_state: dict, kickoff_text: str) -> dict:
    """Runs one or more agents sequentially against a fresh session, seeded
    with `initial_state`, and returns the final session state.

    A fresh `InMemoryRunner`+session per call is enough here - the model
    connection is stateless HTTP to LM Studio, so there's no persistent
    session worth keeping alive across calls.
    """
    agent = agents[0] if len(agents) == 1 else SequentialAgent(name="stage_pipeline", sub_agents=agents)
    runner = InMemoryRunner(agent=agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id=USER_ID, state=initial_state
    )
    kickoff = types.Content(role="user", parts=[types.Part(text=kickoff_text)])
    async for _event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=kickoff):
        pass

    final_session = await runner.session_service.get_session(
        app_name=runner.app_name, user_id=USER_ID, session_id=session.id
    )
    return final_session.state if final_session else {}


async def run_lesson_plan_stage(
    selection: TeacherSelection,
    classroom_context: ClassroomContext,
    manual_topic: Optional[str] = None,
    force_custom: bool = False,
) -> tuple[CurriculumMatch, LessonPlanSections]:
    """Stage 1: match the curriculum (no LLM), then generate the Lesson Plan.

    A manual topic is checked against `services/content_safety.py` before
    anything else happens - this is the authoritative enforcement point, so
    a disallowed topic is blocked here regardless of which caller (frontend,
    tests, a future API) reached it.
    """
    if manual_topic:
        check_topic_safety(manual_topic)

    store = get_store()
    match = store.match_selection(
        grade=selection.grade,
        subject=selection.subject,
        strand=selection.strand,
        unit=selection.unit,
        topic=selection.topic,
        manual_topic=manual_topic,
        force_custom=force_custom,
    )
    logger.info("stage 1/3 curriculum_matching: status=%s record_id=%s", match.match_status, match.record_id)

    model = get_local_model()
    initial_state = {
        "curriculum_match": json.dumps(match.model_dump(), indent=2),
        "selection": json.dumps(selection.model_dump(), indent=2),
        "classroom_context": json.dumps(classroom_context.model_dump(), indent=2),
    }
    state = await _run_agents(
        [build_lesson_planning_agent(model)], initial_state, "Generate the Lesson Plan for this lesson."
    )
    lesson_plan = parse_markdown(sanitize_dollar_signs(state.get("lesson_plan_raw", "")), LessonPlanSections)
    _backfill_benchmark_and_standard(lesson_plan, match)
    logger.info("stage 1/3 lesson_planning: done")
    return match, lesson_plan


def _backfill_benchmark_and_standard(lesson_plan: LessonPlanSections, match: CurriculumMatch) -> None:
    """Guarantees the Benchmark and Content Standard fields literally contain
    their official codes, instead of relying on the model to always
    transcribe them correctly.

    The skill already instructs the model to lead each field with its code
    (see skills/lesson-plan-writing/SKILL.md), but a small local model still
    sometimes writes only the description and drops the code - a small
    model's instruction-following is probabilistic, not contractual. The app
    already knows the correct code with certainty from the matched
    curriculum record, so this enforces it in code rather than just
    detecting its absence after the fact (see services/review.py's matching
    check, which this makes redundant for `exact` matches specifically).
    """
    if match.match_status != "exact" or not match.curriculum_record:
        return
    record = match.curriculum_record

    benchmark_code = record.get("benchmark_code", "")
    if benchmark_code and benchmark_code not in lesson_plan.benchmark:
        lesson_plan.benchmark = f"{benchmark_code} - {lesson_plan.benchmark}".strip(" -")

    content_standard_code = record.get("content_standard_code", "")
    if content_standard_code and content_standard_code not in lesson_plan.content_standard:
        lesson_plan.content_standard = f"{content_standard_code} - {lesson_plan.content_standard}".strip(" -")


async def run_activities_notes_stage(
    match: CurriculumMatch,
    selection: TeacherSelection,
    classroom_context: ClassroomContext,
    lesson_plan_raw: str,
) -> tuple[ActivitiesSections, TeacherNotesSections]:
    """Stage 2: Activities then Teacher Notes, given the already-generated
    Lesson Plan - no re-matching, no re-planning.
    """
    model = get_local_model()
    initial_state = {
        "curriculum_match": json.dumps(match.model_dump(), indent=2),
        "selection": json.dumps(selection.model_dump(), indent=2),
        "classroom_context": json.dumps(classroom_context.model_dump(), indent=2),
        "lesson_plan_raw": lesson_plan_raw,
    }
    state = await _run_agents(
        [build_activities_agent(model), build_teacher_notes_agent(model)],
        initial_state,
        "Generate the Lesson Activities and Teacher Notes for this lesson.",
    )
    activities = parse_markdown(sanitize_dollar_signs(state.get("activities_raw", "")), ActivitiesSections)
    teacher_notes = parse_markdown(sanitize_dollar_signs(state.get("teacher_notes_raw", "")), TeacherNotesSections)
    logger.info("stage 2/3 activities_and_notes: done")
    return activities, teacher_notes


async def run_assessment_stage(
    match: CurriculumMatch,
    selection: TeacherSelection,
    classroom_context: ClassroomContext,
    lesson_plan_raw: str,
    activities_raw: str = "",
    teacher_notes_raw: str = "",
    assessment_mode: str = "full_pack",
) -> AssessmentSections:
    """Stage 3: Tests and assignments, given the already-generated Lesson Plan
    and (since the wizard is meant to build up page over page) the Activities
    and Teacher Notes from stage 2 too - not just the Lesson Plan.
    """
    model = get_local_model()
    initial_state = {
        "curriculum_match": json.dumps(match.model_dump(), indent=2),
        "selection": json.dumps(selection.model_dump(), indent=2),
        "classroom_context": json.dumps(classroom_context.model_dump(), indent=2),
        "lesson_plan_raw": lesson_plan_raw,
        "activities_raw": activities_raw,
        "teacher_notes_raw": teacher_notes_raw,
        "assessment_mode": assessment_mode,
    }
    state = await _run_agents(
        [build_assessment_agent(model)], initial_state, "Generate the Tests and Assignments for this lesson."
    )
    logger.info("stage 3/3 assessment: done")
    return parse_markdown(sanitize_dollar_signs(state.get("assessment_raw", "")), AssessmentSections)
