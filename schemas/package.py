"""The teacher's lesson package, accumulated one wizard stage at a time.

Not constructed all at once - the frontend creates one instance after stage 1
(Lesson Plan) and mutates it in place (`package.activities = ...`,
`package.assessment = ...`) as later stages complete, since none of these
fields are frozen.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .curriculum import ClassroomContext, CurriculumMatch, TeacherSelection
from .review import ReviewResult
from .sections import ActivitiesSections, AssessmentSections, LessonPlanSections, TeacherNotesSections


class ResourcePackage(BaseModel):
    selection: TeacherSelection
    classroom_context: ClassroomContext
    match: CurriculumMatch
    lesson_plan: Optional[LessonPlanSections] = None
    activities: Optional[ActivitiesSections] = None
    teacher_notes: Optional[TeacherNotesSections] = None
    assessment: Optional[AssessmentSections] = None
    review: ReviewResult = Field(default_factory=ReviewResult)
    custom_topic_notice: Optional[str] = None
