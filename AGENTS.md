# AGENTS.md - Project DNA

Shared cross-tool instructions for any coding agent working in this repository.
For *what* the system must do, see [`specs/png-grade9-math-agent-workflow.md`](specs/png-grade9-math-agent-workflow.md)
- that's the source of truth for the workflow and guardrails. This file is
about *how* to work on it.

## Hard constraints

- **Offline only.** No outbound network calls except to `http://localhost:1234`
  (LM Studio). LiteLLM itself attempts one outbound call on startup (fetching
  a model-cost map from GitHub) and falls back to a local copy when it fails -
  that's dependency behavior, not project code.
- **Never guess the model id.** `gemma-4-e2b-it-qat` must be loaded in LM
  Studio. If it needs to change, verify against the running instance's
  `http://localhost:1234/v1/models`, not training-data knowledge.
- **Curriculum facts come from `data/curriculum/png/grade_9/` only.** No
  agent, prompt, or skill should hardcode a benchmark code, strand, unit, or
  learning objective. Curriculum Matching is plain Python with no LLM
  involved, specifically so this can never be a prompt-following problem.
- **Grade and subject are parameters, not constants.** No agent, prompt, or
  skill should reference "Grade 9" or "Mathematics" - they read whatever the
  teacher's selection and matched curriculum record contain. The fact that
  only Grade 9 Math data is loaded today is a data-loading limitation
  (`services/curriculum_store.py`'s `DATA_DIR`, and `GRADE`/`SUBJECT`
  constants in `frontend/app.py`), not an agent-layer one.

## Skills architecture

The agent layer is built around ADK Agent Skills, not large inlined prompts.
The split:

- **`skills/*/SKILL.md`** holds static, reusable procedural knowledge - rules
  about *how* to write a given resource type, and (for the four task skills)
  an `assets/template.md` with the exact output heading structure.
- **`prompts/*.md`** holds only per-request runtime data (`{curriculum_match}`,
  `{selection}`, `{classroom_context}`, prior stages' raw text) plus a
  directive to call `load_skill`/`load_skill_resource` before writing.

Skills can't contain per-request data - if something needs to vary by
request, it belongs in the prompt's data block, not in a skill, even if that
means a skill references a JSON field name (e.g. `match_status`) rather than
a literal value.

Each agent's `SkillToolset` (built via `agents/_shared.py::build_skill_toolset()`)
is scoped to exactly two skills: the shared `png-classroom-conventions` skill
plus that agent's own task skill - never the full skill library. This is
deliberate: a wider, shared `SkillToolset` would mean every agent sees every
skill and has to pick the right one via `list_skills`/description matching,
which reintroduces ambiguity and over-calling risk on a 2-4B local model.
`tests/test_agent_skill_wiring.py` enforces this stays true.

Adding a fifth resource type (e.g. Worksheet, dropped from this rebuild)
means a new `skills/<name>-writing/` directory, a thin `prompts/<name>.md`,
and an `agents/<name>.py` following the existing four as a template - not a
change to the shared skill or the orchestrator's stage-running mechanism.

## The core house rule: code backstops, not prompt-only promises

Prompt-only instructions have repeatedly not held for this model, even when
explicit:

1. The model has skipped a required heading (e.g. "Lesson Title") while
   writing every other section in full - not caught by a whole-document
   emptiness check, since the document as a whole was substantial. Fixed by
   `services/review.py::_check_required_fields`, which checks specific
   always-required fields individually, not just the section as a whole.
2. It has omitted a benchmark code's literal text even when told to include
   it - caught by `_check_record_alignment`'s literal substring check, not
   prevented by the instruction alone.
3. It has used `$...$` LaTeX math notation (this app's renderers don't support
   LaTeX) and `$` for currency (PNG uses Kina/`K`) until the shared skill gave
   concrete examples of the plain-text form to use instead of an abstract
   "don't do X" rule.
4. Running resource-generation agents concurrently via `ParallelAgent`
   exceeded LM Studio's shared context budget - fixed structurally, the
   pipeline never dispatches agents concurrently, only sequentially.

**Default assumption for this model: anything that must always be true needs
a code-level check, not just a clearer instruction.** When prompt-tightening
is tried, treat it as probabilistic improvement and verify it against a live
model run - don't assume a wording fix closed the gap. If something keeps
recurring after tightening, give the Review Agent a deterministic check for
it instead of iterating on wording further.

## Citation rule

Citations are built in code (`format_curriculum_source()` in
`frontend/resource_utils.py`) from the matched curriculum record's
`source_refs` field - never composed or transcribed by the model.

## Code style

- Keep agent prompts in `prompts/*.md` and skill content in `skills/*/SKILL.md`
  - not inlined in `agents/*.py`.
- Keep curriculum matching, alignment review, and content safety in
  `services/` as plain, deterministic Python - don't move any of them into
  an LLM prompt "to make it more flexible."
- Keep Streamlit-coupled code (`frontend/app.py`) separate from pure logic
  (`frontend/resource_utils.py`, importable and testable without a running
  Streamlit session).
