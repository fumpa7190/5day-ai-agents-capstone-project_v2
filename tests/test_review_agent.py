from schemas.curriculum import ClassroomContext, CurriculumMatch, TeacherSelection
from schemas.sections import ActivitiesSections, LessonPlanSections, TeacherNotesSections
from services.review import check_alignment


def _record():
    return {
        "grade": 9,
        "subject": "Mathematics",
        "strand": "Patterns and Algebra",
        "unit": "Linear Functions",
        "benchmark_code": "9.3.3.3",
        "content_standard_code": "CS3",
    }


def _aligned_lesson_plan():
    # Populates every field _check_required_fields now expects, not just the
    # two fields the alignment checks themselves care about - otherwise this
    # fixture would trip the new check and the "pass" assertion would fail.
    return LessonPlanSections(
        lesson_title="Linear Relations in Real Life",
        grade="9",
        subject="Mathematics",
        strand="Patterns and Algebra",
        unit="Linear Functions",
        topic="Linear Relations",
        benchmark="9.3.3.3",
        content_standard="CS3",
        learning_objectives="Students will be able to interpret linear relations.",
        raw_markdown="## Benchmark\n9.3.3.3\n## Content Standard\nCS3\n" * 5,
    )


def test_pass_when_aligned():
    match = CurriculumMatch(match_status="exact", record_id="x", curriculum_record=_record())
    selection = TeacherSelection(
        grade=9, subject="Mathematics", strand="Patterns and Algebra", unit="Linear Functions", topic="Linear Relations"
    )
    context = ClassroomContext(duration="40 minutes", resources=["Blackboard only", "Exercise books"])

    result = check_alignment(match, selection, context, {"lesson_plan": _aligned_lesson_plan()})

    assert result.alignment_status == "pass"
    assert result.issues == []


def test_needs_review_on_benchmark_mismatch():
    match = CurriculumMatch(match_status="exact", record_id="x", curriculum_record=_record())
    selection = TeacherSelection(grade=9, subject="Mathematics")
    context = ClassroomContext(duration="40 minutes", resources=["Blackboard only"])
    lesson_plan = LessonPlanSections(
        benchmark="9.9.9.9", content_standard="CS3", raw_markdown="some unrelated content " * 5
    )

    result = check_alignment(match, selection, context, {"lesson_plan": lesson_plan})

    assert result.alignment_status == "needs_review"
    assert any("benchmark code" in issue for issue in result.issues)


def test_needs_review_on_content_standard_mismatch():
    match = CurriculumMatch(match_status="exact", record_id="x", curriculum_record=_record())
    selection = TeacherSelection(grade=9, subject="Mathematics")
    context = ClassroomContext(duration="40 minutes", resources=["Blackboard only"])
    lesson_plan = LessonPlanSections(
        benchmark="9.3.3.3", content_standard="CS1", raw_markdown="some unrelated content " * 5
    )

    result = check_alignment(match, selection, context, {"lesson_plan": lesson_plan})

    assert result.alignment_status == "needs_review"
    assert any("content standard code" in issue for issue in result.issues)


def test_needs_review_on_forbidden_resource():
    match = CurriculumMatch(match_status="custom")
    selection = TeacherSelection(grade=9, subject="Mathematics", manual_topic="x")
    context = ClassroomContext(duration="40 minutes", resources=["Blackboard only"])
    activities = ActivitiesSections(raw_markdown="Use a calculator to check your answer. " * 5)

    result = check_alignment(match, selection, context, {"activities": activities})

    assert result.alignment_status == "needs_review"
    assert any("calculator" in issue for issue in result.issues)


def test_needs_review_on_empty_section():
    match = CurriculumMatch(match_status="custom")
    selection = TeacherSelection(grade=9, subject="Mathematics", manual_topic="x")
    context = ClassroomContext(duration="40 minutes", resources=["Blackboard only"])
    lesson_plan = LessonPlanSections(raw_markdown="")

    result = check_alignment(match, selection, context, {"lesson_plan": lesson_plan})

    assert result.alignment_status == "needs_review"
    assert any("lesson_plan" in issue for issue in result.issues)


def test_needs_review_on_missing_lesson_title():
    # Reproduces a real observed model behavior: every other lesson plan
    # field was written, but "## Lesson Title" specifically was skipped.
    # _check_nonempty_sections alone can't catch this - the document as a
    # whole is long - which is exactly why _check_required_fields exists.
    match = CurriculumMatch(match_status="custom")
    selection = TeacherSelection(grade=9, subject="Mathematics", manual_topic="x")
    context = ClassroomContext(duration="40 minutes", resources=["Blackboard only"])
    lesson_plan = LessonPlanSections(
        grade="9",
        subject="Mathematics",
        strand="S",
        unit="U",
        topic="T",
        benchmark="some benchmark text",
        content_standard="some content standard text",
        learning_objectives="some objectives",
        raw_markdown="## Grade\n9\n" + "padding " * 20,
    )

    result = check_alignment(match, selection, context, {"lesson_plan": lesson_plan})

    assert result.alignment_status == "needs_review"
    assert any("lesson_title" in issue for issue in result.issues)


def test_needs_review_on_missing_teacher_notes_field():
    match = CurriculumMatch(match_status="custom")
    selection = TeacherSelection(grade=9, subject="Mathematics", manual_topic="x")
    context = ClassroomContext(duration="40 minutes", resources=["Blackboard only"])
    notes = TeacherNotesSections(
        key_concepts="k",
        simple_explanation="s",
        common_student_mistakes="m",
        teaching_tips="t",
        raw_markdown="## Key Concepts\nk\n" + "padding " * 20,
    )

    result = check_alignment(match, selection, context, {"teacher_notes": notes})

    assert result.alignment_status == "needs_review"
    assert any("worked_examples" in issue for issue in result.issues)


def test_pass_does_not_flag_optional_local_context_example():
    # local_context_example is deliberately omittable per
    # teacher-notes-writing's own rules - it must never trigger a
    # required-field issue, unlike the other teacher_notes fields.
    match = CurriculumMatch(match_status="custom")
    selection = TeacherSelection(grade=9, subject="Mathematics", manual_topic="x")
    context = ClassroomContext(duration="40 minutes", resources=["Blackboard only"])
    notes = TeacherNotesSections(
        key_concepts="k" * 10,
        simple_explanation="s" * 10,
        worked_examples="w" * 10,
        common_student_mistakes="m" * 10,
        teaching_tips="t" * 10,
        local_context_example="",
        raw_markdown="## Key Concepts\n" + "padding " * 20,
    )

    result = check_alignment(match, selection, context, {"teacher_notes": notes})

    assert result.alignment_status == "pass"
    assert result.issues == []
