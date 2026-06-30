"""Deterministic Review and Alignment checks (spec section 5.7).

No LLM call - alignment is checked the same way for every run, so a teacher
can trust that a "pass" means the same thing every time, and so this stays
fast against a slow local model (see plan decision 4).
"""

import re

from pydantic import BaseModel

from schemas.curriculum import ClassroomContext, CurriculumMatch, TeacherSelection
from schemas.review import ReviewResult

FORBIDDEN_DEFAULTS = {"internet", "projector", "printer", "calculator"}
MIN_SECTION_CHARS = 30
SHORT_LESSON_MINUTES = 20
SHORT_LESSON_WORD_LIMIT = 600

# These assessment headings are meant to hold actual items (questions a
# student answers), not just framing prose - unlike Marking Guide or Rubric,
# which can legitimately be a short list of criteria.
ASSESSMENT_ITEM_FIELDS = ["quick_quiz", "exit_ticket", "short_test", "assignment"]
_NUMBERED_ITEM_RE = re.compile(r"(?m)^\s*\d+[.)]")

# Some fields (e.g. grade is just "9") are intentionally short, so
# MIN_SECTION_CHARS doesn't apply - these just need to be non-empty. Unlike the
# whole-document check in _check_nonempty_sections, this catches the case where
# the model skips one specific heading while still writing a substantial
# response overall. Only fields that are *unconditionally* required belong
# here - e.g. teacher_notes' local_context_example is deliberately omittable
# per its skill's own rules, so it's excluded. assessment isn't covered yet -
# its required fields depend on assessment_mode, which needs separate handling.
REQUIRED_FIELDS_BY_SECTION = {
    "lesson_plan": [
        "lesson_title",
        "grade",
        "subject",
        "strand",
        "unit",
        "topic",
        "benchmark",
        "content_standard",
        "learning_objectives",
    ],
    "teacher_notes": [
        "key_concepts",
        "simple_explanation",
        "worked_examples",
        "common_student_mistakes",
        "teaching_tips",
    ],
}


def check_alignment(
    match: CurriculumMatch,
    selection: TeacherSelection,
    classroom_context: ClassroomContext,
    sections: dict[str, BaseModel | None],
) -> ReviewResult:
    issues: list[str] = []
    fixes: list[str] = []

    record = match.curriculum_record
    if record:
        _check_record_alignment(record, selection, sections, issues, fixes)

    _check_forbidden_resources(classroom_context, sections, issues, fixes)
    _check_nonempty_sections(sections, issues, fixes)
    _check_required_fields(sections, issues, fixes)
    _check_assessment_has_questions(sections, issues, fixes)
    _check_no_dollar_signs(sections, issues, fixes)
    _check_duration_sanity(classroom_context, sections, issues, fixes)

    status = "needs_review" if issues else "pass"
    return ReviewResult(alignment_status=status, issues=issues, suggested_fixes=fixes)


def _check_record_alignment(
    record: dict,
    selection: TeacherSelection,
    sections: dict[str, BaseModel | None],
    issues: list[str],
    fixes: list[str],
) -> None:
    if record.get("grade") != selection.grade:
        issues.append(
            f"Matched record grade {record.get('grade')} does not match selected grade {selection.grade}."
        )
        fixes.append("Re-run curriculum matching for the correct grade.")

    if record.get("subject", "").lower() != selection.subject.lower():
        issues.append(
            f"Matched record subject '{record.get('subject')}' does not match selected subject "
            f"'{selection.subject}'."
        )
        fixes.append("Re-run curriculum matching for the correct subject.")

    if selection.strand and record.get("strand") != selection.strand:
        issues.append(
            f"Matched record strand '{record.get('strand')}' does not match selected strand "
            f"'{selection.strand}'."
        )
        fixes.append("Confirm the strand selection matches the matched curriculum record.")

    if selection.unit and record.get("unit") != selection.unit:
        issues.append(
            f"Matched record unit '{record.get('unit')}' does not match selected unit '{selection.unit}'."
        )
        fixes.append("Confirm the unit selection matches the matched curriculum record.")

    lesson_plan = sections.get("lesson_plan")
    benchmark_code = record.get("benchmark_code", "")
    if benchmark_code and lesson_plan is not None:
        haystack = f"{getattr(lesson_plan, 'benchmark', '')} {getattr(lesson_plan, 'raw_markdown', '')}"
        if benchmark_code not in haystack:
            issues.append(f"Lesson plan does not reference benchmark code {benchmark_code}.")
            fixes.append("Regenerate the lesson plan, ensuring the benchmark code is included.")

    content_standard_code = record.get("content_standard_code", "")
    if content_standard_code and lesson_plan is not None:
        haystack = (
            f"{getattr(lesson_plan, 'content_standard', '')} {getattr(lesson_plan, 'raw_markdown', '')}"
        )
        if content_standard_code not in haystack:
            issues.append(f"Lesson plan does not reference content standard code {content_standard_code}.")
            fixes.append("Regenerate the lesson plan, ensuring the content standard code is included.")


def _check_forbidden_resources(
    classroom_context: ClassroomContext,
    sections: dict[str, BaseModel | None],
    issues: list[str],
    fixes: list[str],
) -> None:
    available = {r.lower() for r in classroom_context.resources}
    forbidden = FORBIDDEN_DEFAULTS - available
    if not forbidden:
        return
    combined_text = " ".join(
        getattr(section, "raw_markdown", "").lower() for section in sections.values() if section is not None
    )
    for word in sorted(forbidden):
        if word in combined_text:
            issues.append(
                f"Generated content mentions '{word}', which was not listed as an available classroom resource."
            )
            fixes.append(f"Remove or replace the activity/material requiring '{word}' with a low-resource alternative.")


def _check_nonempty_sections(
    sections: dict[str, BaseModel | None],
    issues: list[str],
    fixes: list[str],
) -> None:
    for name, section in sections.items():
        if section is None:
            continue
        if len(getattr(section, "raw_markdown", "").strip()) < MIN_SECTION_CHARS:
            issues.append(f"The '{name}' section looks empty or failed to generate.")
            fixes.append(f"Retry generating the '{name}' section.")


def _check_required_fields(
    sections: dict[str, BaseModel | None],
    issues: list[str],
    fixes: list[str],
) -> None:
    for name, required_fields in REQUIRED_FIELDS_BY_SECTION.items():
        section = sections.get(name)
        if section is None:
            continue
        for field in required_fields:
            if not getattr(section, field, "").strip():
                issues.append(f"The '{name}' section is missing its '{field}' heading/content.")
                fixes.append(
                    f"Regenerate the '{name}' section, ensuring the '{field}' heading and its content are included."
                )


def _check_assessment_has_questions(
    sections: dict[str, BaseModel | None],
    issues: list[str],
    fixes: list[str],
) -> None:
    """Catches an assessment heading that the model wrote but populated with
    only framing prose ("This quiz checks whether students...") and no actual
    questions. `_check_nonempty_sections` only catches a short *whole
    document*, and `_check_required_fields` doesn't cover assessment (its
    headings are mode-dependent, so we can't require any one of them be
    present) - this instead checks that any item-style heading the model did
    choose to write actually contains items, via a numbered-list marker or a
    question mark.
    """
    assessment = sections.get("assessment")
    if assessment is None:
        return
    for field in ASSESSMENT_ITEM_FIELDS:
        content = getattr(assessment, field, "")
        if not content.strip():
            continue
        if not (_NUMBERED_ITEM_RE.search(content) or "?" in content):
            issues.append(f"The '{field}' section doesn't appear to contain any actual questions.")
            fixes.append(f"Regenerate the '{field}' section, ensuring it includes the actual quiz/test questions.")


def _check_no_dollar_signs(
    sections: dict[str, BaseModel | None],
    issues: list[str],
    fixes: list[str],
) -> None:
    """Catches a literal '$' anywhere in generated content.

    Per png-classroom-conventions, '$' should never appear at all: currency
    must use 'K' (Kina), and LaTeX math delimiters ('$...$') aren't
    supported by this app's Markdown-to-Word/PDF pipeline - either use shows
    up as a literal, unrendered '$' in the exported document, so a single
    rule ("no '$' anywhere") catches both failure modes without needing to
    tell them apart.
    """
    for name, section in sections.items():
        if section is None:
            continue
        if "$" in getattr(section, "raw_markdown", ""):
            issues.append(
                f"The '{name}' section contains a literal '$', which won't render correctly "
                "(currency should use 'K', and math should be written in plain text, not LaTeX)."
            )
            fixes.append(f"Regenerate the '{name}' section without any '$' - use 'K' for currency and plain text for math.")


def _check_duration_sanity(
    classroom_context: ClassroomContext,
    sections: dict[str, BaseModel | None],
    issues: list[str],
    fixes: list[str],
) -> None:
    duration_match = re.search(r"(\d+)", classroom_context.duration or "")
    if not duration_match:
        return
    minutes = int(duration_match.group(1))
    if minutes > SHORT_LESSON_MINUTES:
        return
    total_words = sum(
        len(getattr(section, "raw_markdown", "").split()) for section in sections.values() if section is not None
    )
    if total_words > SHORT_LESSON_WORD_LIMIT:
        issues.append(
            f"Generated content ({total_words} words) may be too long for a {minutes}-minute lesson."
        )
        fixes.append("Trim activities to fit the available class time.")
