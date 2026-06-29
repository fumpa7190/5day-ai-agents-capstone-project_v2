import asyncio
import sys
from pathlib import Path

import markdown as md
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator.pipeline import (  # noqa: E402
    run_activities_notes_stage,
    run_assessment_stage,
    run_lesson_plan_stage,
)
from schemas.curriculum import ClassroomContext, CurriculumMatch, TeacherSelection  # noqa: E402
from schemas.package import ResourcePackage  # noqa: E402
from services import review as review_service  # noqa: E402
from services.content_safety import UnsafeTopicError, check_topic_safety  # noqa: E402
from services.curriculum_store import get_store  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resource_utils import (  # noqa: E402
    load_school_name,
    markdown_to_docx_bytes,
    markdown_to_pdf_bytes,
    render_package_markdown,
    render_section_markdown,
    save_school_name,
)

GENERATION_TIMEOUT_SECONDS = 300

# Grade and subject are parameters of the agent/skill layer (see
# specs/png-grade9-math-agent-workflow.md section 1) - they are not fixed
# here because the system can't do them, only because this is the only
# grade/subject with curriculum data actually loaded today. Add another
# grade's data in the same format and this becomes a selector, not a const.
GRADE = 9
SUBJECT = "Mathematics"
RESOURCE_AVAILABILITY_OPTIONS = ["Blackboard only", "Exercise books", "Textbooks", "Calculator", "Internet"]
ABILITY_OPTIONS = ["Mixed", "Low", "High"]
LANGUAGE_LEVEL_OPTIONS = ["Simple English", "Standard English", "Tok Pisin support"]

WIZARD_KEYS = (
    "package",
    "awaiting_confirmation",
    "pending_match",
    "pending_manual_topic",
    "pending_classroom_context",
)

st.set_page_config(page_title="PNG Classroom Resource Generator", layout="centered")

PNG_THEME_CSS = """
<style>
:root {
    --png-black: #161616;
    --png-red: #CE1126;
    --png-red-dark: #9c0d1c;
    --png-gold: #F8C300;
}
.stApp { background-color: #faf8f3; }
[data-testid="stHeader"] {
    background-color: var(--png-black);
}
.app-title-bar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 999;
    padding: 0.6rem 1rem;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: var(--png-gold);
}
.png-header {
    background: linear-gradient(135deg, var(--png-black) 0%, #2b2b2b 100%);
    border-bottom: 6px solid var(--png-red);
    border-radius: 14px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.5rem;
}
.png-header h1 {
    color: var(--png-gold);
    margin: 0;
    font-size: 1.6rem;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}
.png-header .school-name {
    color: #ffffff;
    margin: 0.3rem 0 0 0;
    font-size: 1.15rem;
    font-weight: 600;
}
.png-header p {
    color: #cccccc;
    margin: 0.5rem 0 0 0;
    font-size: 0.9rem;
}
.result-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 2rem;
    box-shadow: 0 2px 14px rgba(0,0,0,0.08);
    border-top: 5px solid var(--png-red);
    margin-bottom: 1.2rem;
}
.result-card h3 {
    color: #161616;
    margin-top: 0;
}
.result-card p, .result-card li {
    line-height: 1.6;
    margin-bottom: 0.6rem;
}
.result-card h1, .result-card h2 {
    color: #161616;
    margin-top: 1.2rem;
}
.result-card ul, .result-card ol {
    margin-bottom: 1rem;
}
.result-card table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
}
.result-card th, .result-card td {
    border: 1px solid #ddd;
    padding: 0.4rem 0.6rem;
    text-align: left;
}
.result-card th {
    background-color: var(--png-black);
    color: white;
}
div[data-testid="stForm"] {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.5rem 1.5rem 0.5rem 1.5rem;
    box-shadow: 0 2px 14px rgba(0,0,0,0.06);
}
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background-color: var(--png-red);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.2rem;
}
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: var(--png-red-dark);
    color: white;
}
div[data-testid="stDownloadButton"] > button {
    background-color: var(--png-black);
    color: var(--png-gold);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.2rem;
    width: 100%;
}
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:focus,
div[data-testid="stDownloadButton"] > button:active {
    background-color: #2b2b2b;
    color: var(--png-gold);
    border: none;
}
</style>
"""
st.markdown(PNG_THEME_CSS, unsafe_allow_html=True)
st.markdown('<div class="app-title-bar">PNG Classroom Resource Generator</div>', unsafe_allow_html=True)


def run_async(coro):
    return asyncio.run(asyncio.wait_for(coro, timeout=GENERATION_TIMEOUT_SECONDS))


def run_stage(coro, what: str):
    """Runs a stage's coroutine, returning its result - or showing a friendly
    error and returning None instead of letting an unhandled exception crash
    the Streamlit script. Each later stage carries more text forward from
    earlier ones, and that's occasionally been enough to exceed the local
    model's context limit (`litellm.BadRequestError: Context size has been
    exceeded`) even though no single stage's own prompt is unreasonable -
    this is a real, observed failure mode, not just a timeout.
    """
    try:
        return run_async(coro)
    except TimeoutError:
        st.error(f"{what} did not finish within {GENERATION_TIMEOUT_SECONDS} seconds and was stopped. Try again.")
        return None
    except UnsafeTopicError as e:
        # Defense in depth: the frontend's manual-topic submit handler already
        # checks this up front, but run_lesson_plan_stage enforces it too, for
        # any caller that reaches it without going through that check first.
        st.error(str(e))
        return None
    except Exception as e:
        st.error(
            f"{what} ran into a problem and could not finish ({e}). This can happen when the "
            "lesson content carried forward from earlier steps is unusually long for the local "
            "model. Try again - if it keeps happening, try a shorter lesson duration."
        )
        return None


def _is_unsafe_topic(manual_topic: str) -> bool:
    """Checks a manual topic up front, before any curriculum matching or
    spinner - so a disallowed topic is rejected immediately rather than
    after a suggestion-confirmation round trip.
    """
    try:
        check_topic_safety(manual_topic)
        return False
    except UnsafeTopicError as e:
        st.error(str(e))
        return True


def clear_wizard():
    for key in WIZARD_KEYS:
        st.session_state.pop(key, None)
    for key in ("last_result", "last_title"):
        st.session_state.pop(key, None)


def render_review_banner(package: ResourcePackage) -> None:
    if package.custom_topic_notice:
        st.info(package.custom_topic_notice)
    if package.review.alignment_status == "needs_review":
        issues = "\n".join(f"- {issue}" for issue in package.review.issues)
        st.warning(f"This output was flagged for review:\n{issues}")


def render_stage_card(title: str, section) -> None:
    html = md.markdown(render_section_markdown(title, section), extensions=["tables", "nl2br"])
    st.markdown(f'<div class="result-card">{html}</div>', unsafe_allow_html=True)


def start_lesson_plan(selection: TeacherSelection, classroom_context: ClassroomContext, **kwargs):
    """Stage 1: curriculum match + Lesson Plan. Builds the ResourcePackage
    that later stages mutate in place.
    """
    clear_wizard()
    result = run_stage(run_lesson_plan_stage(selection, classroom_context, **kwargs), "Generating the Lesson Plan")
    if result is None:
        return
    match, lesson_plan = result

    review_result = review_service.check_alignment(
        match, selection, classroom_context, {"lesson_plan": lesson_plan}
    )
    custom_topic_notice = None
    if match.match_status != "exact":
        custom_topic_notice = (
            "This resource is based on a custom or suggested topic and is not directly "
            "matched to the official extracted PNG curriculum."
        )
    st.session_state.package = ResourcePackage(
        selection=selection,
        classroom_context=classroom_context,
        match=match,
        lesson_plan=lesson_plan,
        review=review_result,
        custom_topic_notice=custom_topic_notice,
    )


def continue_to_activities_notes(package: ResourcePackage) -> None:
    result = run_stage(
        run_activities_notes_stage(
            package.match, package.selection, package.classroom_context, package.lesson_plan.raw_markdown
        ),
        "Generating Lesson Activities and Teacher Notes",
    )
    if result is None:
        return
    activities, teacher_notes = result

    package.activities = activities
    package.teacher_notes = teacher_notes
    package.review = review_service.check_alignment(
        package.match,
        package.selection,
        package.classroom_context,
        {"lesson_plan": package.lesson_plan, "activities": activities, "teacher_notes": teacher_notes},
    )


def continue_to_assessment(package: ResourcePackage) -> None:
    assessment = run_stage(
        run_assessment_stage(
            package.match,
            package.selection,
            package.classroom_context,
            package.lesson_plan.raw_markdown,
            activities_raw=package.activities.raw_markdown,
            teacher_notes_raw=package.teacher_notes.raw_markdown,
        ),
        "Generating Tests and Assignments",
    )
    if assessment is None:
        return

    package.assessment = assessment
    package.review = review_service.check_alignment(
        package.match,
        package.selection,
        package.classroom_context,
        {
            "lesson_plan": package.lesson_plan,
            "activities": package.activities,
            "teacher_notes": package.teacher_notes,
            "assessment": assessment,
        },
    )
    topic_label = package.selection.topic or package.selection.manual_topic or "Custom topic"
    st.session_state.last_result = render_package_markdown(package)
    st.session_state.last_title = f"Lesson Pack - Grade {package.selection.grade} {package.selection.subject} - {topic_label}"


school_name = load_school_name()

if not school_name:
    st.markdown(
        """
        <div class="png-header">
            <h1>Welcome</h1>
            <p>Let's set up the PNG Classroom Resource Generator for your school.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("school_setup_form"):
        name_input = st.text_input("What is your school's name?", placeholder="e.g. Sogeri National High School")
        start_submitted = st.form_submit_button("Get Started")

    if start_submitted:
        if name_input.strip():
            save_school_name(name_input.strip())
            st.rerun()
        else:
            st.error("Please enter a school name.")
    st.stop()

with st.sidebar:
    with st.expander("Settings"):
        edited_name = st.text_input("School name", value=school_name)
        if st.button("Update school name"):
            if edited_name.strip():
                save_school_name(edited_name.strip())
                st.rerun()

st.markdown(
    f"""
    <div class="png-header">
        <h1>PNG Classroom Resource Generator</h1>
        <p class="school-name">{school_name}</p>
        <p>This AI assistant walks you through preparing a lesson step by step -
        Lesson Plan, then Activities &amp; Teacher Notes, then Tests &amp;
        Assignments - grounded in the real PNG Standards-Based Curriculum
        (Syllabus + Teacher Guide).</p>
        <p style="font-style: italic;">Please review and verify each generated section before
        using it in class - AI-generated content can contain mistakes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

package: ResourcePackage | None = st.session_state.get("package")
if package is not None:
    if st.button("Start Over"):
        clear_wizard()
        st.rerun()

store = get_store()

# ---------------------------------------------------------------------------
# Step 1: curriculum selection -> Lesson Plan
# ---------------------------------------------------------------------------
if package is None:
    selection_tree = store.get_selection_tree().get(str(GRADE), {}).get(SUBJECT, {})

    st.subheader("Step 1: Select the curriculum topic and generate a Lesson Plan")
    st.caption(f"Grade {GRADE} - {SUBJECT} (the only grade/subject with curriculum data loaded today)")

    manual_mode = st.checkbox("My topic isn't listed - let me type it in", key="manual_mode")

    strand = unit = None
    selected_topic_entry = None
    manual_topic_text = ""

    if manual_mode:
        manual_topic_text = st.text_input(
            "Manual topic", placeholder="e.g. Pythagorean Theorem, Simple Interest"
        )
    else:
        strand = st.selectbox("Strand", list(selection_tree.keys()), key="sel_strand")
        unit_options = list(selection_tree.get(strand, {}).keys()) if strand else []
        unit = st.selectbox("Unit", unit_options, key="sel_unit")
        topic_entries = selection_tree.get(strand, {}).get(unit, []) if unit else []
        if topic_entries:
            topic_idx = st.selectbox(
                "Topic",
                range(len(topic_entries)),
                format_func=lambda i: f"{topic_entries[i]['topic']} ({topic_entries[i]['benchmark_code']})",
                key="sel_topic_idx",
            )
            selected_topic_entry = topic_entries[topic_idx]
        else:
            st.info("No topics found for this strand/unit.")

    col1, col2 = st.columns(2)
    with col1:
        duration = st.number_input("Lesson duration (minutes)", min_value=10, max_value=120, value=40, step=5)
        ability = st.selectbox("Class ability", ABILITY_OPTIONS)
    with col2:
        resources = st.multiselect(
            "Resources available", RESOURCE_AVAILABILITY_OPTIONS, default=["Blackboard only", "Exercise books"]
        )
        language_level = st.selectbox("Language level", LANGUAGE_LEVEL_OPTIONS)

    def build_classroom_context() -> ClassroomContext:
        return ClassroomContext(
            duration=f"{duration} minutes", ability=ability, resources=resources, language_level=language_level
        )

    if st.session_state.get("awaiting_confirmation"):
        pending_match: CurriculumMatch = st.session_state.pending_match
        st.warning(pending_match.warnings[0] if pending_match.warnings else "No exact curriculum match found.")
        st.write("Did you mean one of these official curriculum topics?")
        for i, suggestion in enumerate(pending_match.suggestions):
            if st.button(f"Use: {suggestion.topic} ({suggestion.benchmark_code})", key=f"confirm_{i}"):
                confirmed_selection = TeacherSelection(
                    grade=GRADE, subject=SUBJECT, strand=suggestion.strand, unit=suggestion.unit, topic=suggestion.topic
                )
                with st.spinner("Generating Lesson Plan..."):
                    start_lesson_plan(confirmed_selection, st.session_state.pending_classroom_context)
                st.rerun()
        if st.button("No, generate it as a custom topic", key="confirm_custom"):
            custom_selection = TeacherSelection(
                grade=GRADE, subject=SUBJECT, manual_topic=st.session_state.pending_manual_topic
            )
            with st.spinner("Generating Lesson Plan..."):
                start_lesson_plan(
                    custom_selection,
                    st.session_state.pending_classroom_context,
                    manual_topic=st.session_state.pending_manual_topic,
                    force_custom=True,
                )
            st.rerun()
    elif st.button("Generate Lesson Plan", type="primary"):
        if manual_mode:
            if not manual_topic_text.strip():
                st.error("Please enter a topic.")
            elif _is_unsafe_topic(manual_topic_text.strip()):
                pass  # error already shown by _is_unsafe_topic
            else:
                quick_match = store.match_selection(grade=GRADE, subject=SUBJECT, manual_topic=manual_topic_text.strip())
                if quick_match.match_status == "suggested":
                    st.session_state.awaiting_confirmation = True
                    st.session_state.pending_match = quick_match
                    st.session_state.pending_manual_topic = manual_topic_text.strip()
                    st.session_state.pending_classroom_context = build_classroom_context()
                    st.rerun()
                else:
                    with st.spinner("Generating Lesson Plan..."):
                        start_lesson_plan(
                            TeacherSelection(grade=GRADE, subject=SUBJECT, manual_topic=manual_topic_text.strip()),
                            build_classroom_context(),
                            manual_topic=manual_topic_text.strip(),
                        )
                    st.rerun()
        elif selected_topic_entry is None:
            st.error("Please choose a topic.")
        else:
            with st.spinner("Generating Lesson Plan..."):
                start_lesson_plan(
                    TeacherSelection(
                        grade=GRADE, subject=SUBJECT, strand=strand, unit=unit, topic=selected_topic_entry["topic"]
                    ),
                    build_classroom_context(),
                )
            st.rerun()

# ---------------------------------------------------------------------------
# Step 1 result + Step 2: Activities & Teacher Notes
# ---------------------------------------------------------------------------
if package is not None:
    render_stage_card("Lesson Plan", package.lesson_plan)
    render_review_banner(package)

    if package.activities is None or package.teacher_notes is None:
        st.subheader("Step 2: Generate Lesson Activities & Teacher Notes")
        st.caption("Built from the Lesson Plan above - no need to re-enter anything.")
        if st.button("Next: Generate Lesson Activities & Teacher Notes", type="primary"):
            with st.spinner("Generating Lesson Activities and Teacher Notes..."):
                continue_to_activities_notes(package)
            st.rerun()

# ---------------------------------------------------------------------------
# Step 2 result + Step 3: Tests & Assignments
# ---------------------------------------------------------------------------
if package is not None and package.activities is not None and package.teacher_notes is not None:
    render_stage_card("Lesson Activities", package.activities)
    render_stage_card("Teacher Notes", package.teacher_notes)
    render_review_banner(package)

    if package.assessment is None:
        st.subheader("Step 3: Generate Tests & Assignments")
        st.caption("Assesses the same learning objectives as the Lesson Plan above.")
        if st.button("Next: Generate Tests & Assignments", type="primary"):
            with st.spinner("Generating Tests and Assignments..."):
                continue_to_assessment(package)
            st.rerun()

# ---------------------------------------------------------------------------
# Step 3 result + export
# ---------------------------------------------------------------------------
if package is not None and package.assessment is not None:
    render_stage_card("Assessment", package.assessment)
    render_review_banner(package)

if "last_result" in st.session_state:
    st.divider()
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        try:
            docx_bytes = markdown_to_docx_bytes(
                st.session_state.last_result, st.session_state.last_title, school_name
            )
            st.download_button(
                "Download as Word",
                data=docx_bytes,
                file_name=f"{st.session_state.last_title.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Could not generate Word document: {e}")
    with dl_col2:
        try:
            pdf_bytes = markdown_to_pdf_bytes(
                st.session_state.last_result, st.session_state.last_title, school_name
            )
            st.download_button(
                "Download as PDF",
                data=pdf_bytes,
                file_name=f"{st.session_state.last_title.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Could not generate PDF: {e}")
