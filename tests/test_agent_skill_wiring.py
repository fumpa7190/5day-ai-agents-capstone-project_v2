"""Each stage agent must only ever see its own skill(s) - the shared PNG
conventions skill plus its own task skill - never the full skill library.
This is the "narrow per-agent SkillToolset" design decision (as opposed to one
shared SkillToolset exposing every skill to every agent), checked here so a
future change can't silently widen an agent's visibility without a test
failing.
"""

from google.adk.tools.skill_toolset import SkillToolset

from agents._shared import get_local_model
from agents.activities import build_activities_agent
from agents.assessment import build_assessment_agent
from agents.lesson_planning import build_lesson_planning_agent
from agents.teacher_notes import build_teacher_notes_agent

MODEL = get_local_model()
SHARED_SKILL = "png-classroom-conventions"


def _skill_names(agent):
    toolsets = [t for t in agent.tools if isinstance(t, SkillToolset)]
    assert len(toolsets) == 1, "expected exactly one SkillToolset on the agent"
    return {skill.name for skill in toolsets[0].skills}


def test_lesson_planning_agent_sees_only_its_own_skills():
    agent = build_lesson_planning_agent(MODEL)
    assert _skill_names(agent) == {SHARED_SKILL, "lesson-plan-writing"}


def test_activities_agent_sees_only_its_own_skills():
    agent = build_activities_agent(MODEL)
    assert _skill_names(agent) == {SHARED_SKILL, "classroom-activities-writing"}


def test_teacher_notes_agent_sees_only_its_own_skills():
    agent = build_teacher_notes_agent(MODEL)
    assert _skill_names(agent) == {SHARED_SKILL, "teacher-notes-writing"}


def test_assessment_agent_sees_only_its_own_skills():
    agent = build_assessment_agent(MODEL)
    assert _skill_names(agent) == {SHARED_SKILL, "assessment-writing"}
