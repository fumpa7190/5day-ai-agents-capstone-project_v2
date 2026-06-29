"""Per-agent output schemas.

Fields mirror the spec's literal "Must produce" lists (specs/png-classroom-agent-workflow.md
sections 5.2-5.6). Each agent writes Markdown headed by these field names; `raw_markdown`
always holds the full, unparsed response so nothing is lost if a heading is missed or
renamed by the model.
"""

from pydantic import BaseModel


class LessonPlanSections(BaseModel):
    lesson_title: str = ""
    grade: str = ""
    subject: str = ""
    strand: str = ""
    unit: str = ""
    topic: str = ""
    benchmark: str = ""
    content_standard: str = ""
    learning_objectives: str = ""
    prior_knowledge: str = ""
    materials: str = ""
    introduction: str = ""
    teacher_activities: str = ""
    student_activities: str = ""
    guided_practice: str = ""
    independent_practice: str = ""
    assessment_for_learning: str = ""
    closure: str = ""
    homework: str = ""
    teacher_reflection: str = ""
    raw_markdown: str = ""


class ActivitiesSections(BaseModel):
    starter_activity: str = ""
    main_activity: str = ""
    group_activity: str = ""
    individual_practice: str = ""
    extension_activity: str = ""
    support_activity: str = ""
    raw_markdown: str = ""


class TeacherNotesSections(BaseModel):
    key_concepts: str = ""
    simple_explanation: str = ""
    worked_examples: str = ""
    common_student_mistakes: str = ""
    teaching_tips: str = ""
    local_context_example: str = ""
    raw_markdown: str = ""


class WorksheetSections(BaseModel):
    student_instructions: str = ""
    example_question: str = ""
    practice_questions: str = ""
    challenge_questions: str = ""
    answer_key: str = ""
    raw_markdown: str = ""


class AssessmentSections(BaseModel):
    quick_quiz: str = ""
    exit_ticket: str = ""
    short_test: str = ""
    assignment: str = ""
    marking_guide: str = ""
    rubric: str = ""
    raw_markdown: str = ""
