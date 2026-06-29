"""Schema for the Review and Alignment Agent's output (spec section 5.7)."""

from pydantic import BaseModel, Field


class ReviewResult(BaseModel):
    alignment_status: str = "pass"  # "pass" | "needs_review"
    issues: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)
