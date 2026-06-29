"""Schemas for the teacher's selection and the Curriculum Matching Agent's output."""

from typing import Optional

from pydantic import BaseModel, Field


class ClassroomContext(BaseModel):
    duration: str = ""
    ability: str = ""
    resources: list[str] = Field(default_factory=list)
    language_level: str = ""
    uploaded_resources: list[str] = Field(default_factory=list)


class TeacherSelection(BaseModel):
    grade: int
    subject: str
    strand: Optional[str] = None
    unit: Optional[str] = None
    topic: Optional[str] = None
    manual_topic: Optional[str] = None


class MatchSuggestion(BaseModel):
    record_id: str
    topic: str
    strand: str
    unit: str
    benchmark_code: str
    score: float


class CurriculumMatch(BaseModel):
    match_status: str  # "exact" | "suggested" | "custom"
    record_id: Optional[str] = None
    curriculum_record: Optional[dict] = None
    suggestions: list[MatchSuggestion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
