from schemas.sections import AssessmentSections, LessonPlanSections
from services.markdown_sections import parse

SAMPLE = """## Lesson Title
Linear Relations in Real Life

## Benchmark
9.3.3.3 - Apply and interpret linear relation modelling practical situations.

## Content Standard
CS3 - Students will be able to interpret various types of patterns and functional relationships.

## Materials
- Blackboard
- Exercise books
"""


def test_parse_fills_matching_headings():
    result = parse(SAMPLE, LessonPlanSections)
    assert result.lesson_title == "Linear Relations in Real Life"
    assert "9.3.3.3" in result.benchmark
    assert "CS3" in result.content_standard
    assert "Blackboard" in result.materials


def test_parse_keeps_raw_markdown_fallback():
    result = parse(SAMPLE, LessonPlanSections)
    assert result.raw_markdown.strip() == SAMPLE.strip()


def test_parse_ignores_unrecognized_headings_but_keeps_raw():
    text = "## Not A Real Field\nSome text\n\n## Lesson Title\nMy Title\n"
    result = parse(text, LessonPlanSections)
    assert result.lesson_title == "My Title"
    assert "Not A Real Field" in result.raw_markdown


def test_parse_handles_empty_text():
    result = parse("", LessonPlanSections)
    assert result.lesson_title == ""
    assert result.raw_markdown == ""


def test_parse_concatenates_repeated_headings_instead_of_overwriting():
    # The Assessment agent in "full_pack" mode writes a Marking Guide after
    # each of Quick Quiz/Short Test/Assignment, not one combined one.
    text = (
        "## Quick Quiz\nQ1...\n\n"
        "## Marking Guide\nQuiz marking: 1 mark each.\n\n"
        "## Short Test\nQ2...\n\n"
        "## Marking Guide\nTest marking: 2 marks each.\n"
    )
    result = parse(text, AssessmentSections)
    assert "Quiz marking" in result.marking_guide
    assert "Test marking" in result.marking_guide


def test_parse_keeps_earlier_content_when_a_later_occurrence_is_empty():
    # A genuinely empty later occurrence of a repeated heading must not wipe
    # out an earlier, populated one (this was the actual bug observed live).
    text = (
        "## Marking Guide\nReal marking content here.\n\n"
        "## Quick Quiz\nQ1...\n\n"
        "## Marking Guide\n\n"
        "## Rubric\nSome rubric text.\n"
    )
    result = parse(text, AssessmentSections)
    assert "Real marking content" in result.marking_guide
