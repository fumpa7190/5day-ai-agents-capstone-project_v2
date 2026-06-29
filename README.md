# PNG Classroom Resource Generator (v2 - Agent Skills rebuild)

An AI assistant that helps teachers in Papua New Guinea schools generate lesson
plans, activities, teacher notes, and assessments - grounded in the real PNG
Standards-Based Curriculum, and running entirely on a light local LLM
(`gemma-4-e2b-it-qat` via LM Studio) so it works without a paid cloud API or
reliable internet access.

This is a rebuild of [5day-ai-agents-capstone-project](https://github.com/fumpa7190/5day-ai-agents),
with the agent layer redesigned around **ADK Agent Skills**
(`load_skill_from_dir` / `SkillToolset`) instead of large inlined prompts. The
agent workflow and guardrails are unchanged from the spec; what changed is
where the procedural knowledge each agent follows actually lives.

The implementation follows [`specs/png-grade9-math-agent-workflow.md`](specs/png-grade9-math-agent-workflow.md),
the source of truth for the agent workflow, guardrails, and Definition of Done.
For house rules and the Skills architecture, see [`AGENTS.md`](AGENTS.md).

## How it works

```
Teacher Selection
      |
      Curriculum Matching - deterministic, no LLM (services/curriculum_store.py)
      |
      Lesson Planning Agent - LLM                          [orchestrator/pipeline.py
      |                                                      run_lesson_plan_stage()]
      v  (teacher clicks "Next")
      Activities Agent -> Teacher Notes Agent - LLM, sequential   [run_activities_
      |                                                            notes_stage()]
      v  (teacher clicks "Next")
      Assessment Agent - LLM                                 [run_assessment_stage()]
      |
      v
Review and Alignment - deterministic, no LLM (services/review.py)
      |
Combined Lesson Pack -> rendered, downloadable (Word or PDF)
```

Curriculum Matching and Review are plain Python, not LLM calls - so curriculum
facts can never be invented and alignment checking is identical every run.
Each of the four `LlmAgent`s carries a `SkillToolset` scoped to exactly two
skills: a shared `png-classroom-conventions` skill (resource-availability
defaults, PNG context, currency, plain-text math, mixed-ability, language
level) and one task-specific skill (`lesson-plan-writing`,
`classroom-activities-writing`, `teacher-notes-writing`, or
`assessment-writing`) that defines the output structure and content rules for
that resource type. See `AGENTS.md` for how the Skills layer is structured.

## Folder structure

```
skills/        # ADK Agent Skills - SKILL.md + assets/template.md per skill
prompts/       # thin per-agent instruction shells (runtime data only)
agents/        # LlmAgent factory functions, one per prompt
orchestrator/  # pipeline.py - the three teacher-paced stage functions
services/      # deterministic logic - curriculum matching, review, content safety
schemas/       # Pydantic models for selections, sections, and the final package
data/curriculum/png/grade_9/   # the curriculum data - source of truth
frontend/      # Streamlit wizard UI + Word/PDF export
tests/         # offline, no LM Studio dependency
specs/         # the workflow spec this app implements
```

## Setup & Running

### Prerequisites

- **Python 3.14**.
- **LM Studio** with `gemma-4-e2b-it-qat` (lmstudio-community) downloaded and
  loaded, context length set to at least 16384 (later wizard steps carry
  earlier content forward and can exceed the default 4096-8192).
- LM Studio's local server running and serving at `http://localhost:1234` -
  verify by opening `http://localhost:1234/v1/models` in a browser.

(To use a different model, edit `agents/_shared.py::get_local_model()`.)

### Install

```bash
git clone https://github.com/fumpa7190/5day-ai-agents-capstone-project_v2.git
cd 5day-ai-agents-capstone-project_v2
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Sanity check (no LM Studio needed)

```bash
pytest
```

All 43 tests should pass in well under a second.

### Run

```bash
streamlit run frontend/app.py
```

Opens `http://localhost:8501`. First run asks for a school name, then shows
the Step 1 form. A reliable path to try: leave "My topic isn't listed"
unchecked, pick Strand **Patterns and Algebra** -> Unit **Linear Functions** ->
Topic **Linear Relations**, and click through all three steps.

### Troubleshooting

- **"...ran into a problem...Context size has been exceeded"** - increase the
  model's loaded context length in LM Studio (see Prerequisites).
- **Connection refused / model not found** - confirm
  `http://localhost:1234/v1/models` responds and the loaded model's id
  matches `agents/_shared.py::get_local_model()`.

## Known limitations

- Only Grade 9 Mathematics has curriculum data loaded - a data-loading
  limitation, not an architectural one (see `specs/png-grade9-math-agent-workflow.md`
  section 1).
- A small local model doesn't always follow every instruction (e.g. it has
  skipped a heading, or omitted a literal benchmark code). Where this was
  observed, the relevant skill was tightened and/or the deterministic Review
  Agent was extended to catch it - but prompt-following from a 2-4B model is
  not 100% reliable.
- Worksheet generation was dropped from this rebuild (it existed, unwired, in
  the original project) - it can be added later as a fifth skill + agent
  following the same pattern as the other four.
- Assessment's per-mode required headings (`quiz_test`/`assignment`/`full_pack`)
  aren't checked by the Review Agent the way Lesson Plan's and Teacher Notes'
  always-required fields are - the check would need to be conditional on
  `assessment_mode`, not yet implemented.
