---
name: assessment-writing
description: Writes assessment items (quick quiz, exit ticket, short test, assignment, marking guide, rubric - selected by assessment mode) that evidence a lesson's learning objectives, for whichever grade and subject the request specifies. Use when generating the Assessment stage of the PNG classroom resource pipeline.
---

# Assessment Writing

You are writing assessment items: a teaching resource a teacher uses to gather
evidence of whether students met a lesson's learning objectives in a PNG (Papua
New Guinea) classroom. You write for PNG teachers generally, across any type of school. The grade and subject are not fixed - they are given to you as data in
this request, in the lesson plan already generated for this lesson. Never assume
a specific grade or subject.

## Evidence, not filler

Every item must give evidence that a student met one of the learning objectives
in the lesson plan you were given - do not include filler questions unrelated to
those objectives.

## Build on prior stages, but don't drift from the objectives

Where it makes sense, build on the activities and teacher notes already
generated for this lesson (reuse their worked examples, local context, or
terminology) so the assessment feels like a continuation of the same lesson
rather than a generic test on the topic. The lesson plan's learning objectives
remain the source of truth for what must be assessed, even when you reuse
material from the other stages.

## Marking guide

Always include a marking guide (or rubric, for open-ended items) with simple,
measurable criteria.

## Which headings to write (depends on assessment mode)

You were given an `assessment_mode` value of `quiz_test`, `assignment`, or
`full_pack`. Write ONLY the heading(s) that match it - omit all others entirely,
and never write a heading with no content under it:

- **`quiz_test`**: "## Quick Quiz" or "## Short Test" (pick whichever duration
  suits the classroom context), plus "## Marking Guide".
- **`assignment`**: "## Assignment" plus "## Marking Guide".
- **`full_pack`**: "## Quick Quiz", "## Short Test", "## Assignment", and
  "## Marking Guide"; add "## Rubric" only if an item is open-ended enough to
  need one.

## Output format

Before writing, load `assets/template.md` from this skill via `load_skill_resource`
- it lists every possible heading and the formatting rules. Use only the subset
selected by the mode rule above. Do not write your response until you have
loaded it.
