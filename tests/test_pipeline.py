from orchestrator.pipeline import _backfill_benchmark_and_standard
from schemas.curriculum import CurriculumMatch
from schemas.sections import LessonPlanSections


def _record():
    return {
        "grade": 9,
        "subject": "Mathematics",
        "benchmark_code": "9.2.2.9",
        "content_standard_code": "CS2",
    }


def test_backfills_missing_benchmark_and_standard_codes():
    match = CurriculumMatch(match_status="exact", record_id="x", curriculum_record=_record())
    lesson_plan = LessonPlanSections(
        benchmark="Apply ratios and proportions to real-life situations.",
        content_standard="Students will be able to reason about relationships between quantities.",
    )

    _backfill_benchmark_and_standard(lesson_plan, match)

    assert lesson_plan.benchmark.startswith("9.2.2.9 - ")
    assert lesson_plan.content_standard.startswith("CS2 - ")


def test_does_not_duplicate_a_code_the_model_already_wrote():
    match = CurriculumMatch(match_status="exact", record_id="x", curriculum_record=_record())
    lesson_plan = LessonPlanSections(
        benchmark="9.2.2.9 - Apply ratios and proportions to real-life situations.",
        content_standard="CS2 - Students will be able to reason about relationships between quantities.",
    )

    _backfill_benchmark_and_standard(lesson_plan, match)

    assert lesson_plan.benchmark.count("9.2.2.9") == 1
    assert lesson_plan.content_standard.count("CS2") == 1


def test_does_not_fabricate_a_code_for_a_custom_topic():
    match = CurriculumMatch(match_status="custom")
    lesson_plan = LessonPlanSections(
        benchmark="Custom topic - not directly matched to the official PNG curriculum.",
        content_standard="Custom topic - not directly matched to the official PNG curriculum.",
    )

    _backfill_benchmark_and_standard(lesson_plan, match)

    assert lesson_plan.benchmark == "Custom topic - not directly matched to the official PNG curriculum."
