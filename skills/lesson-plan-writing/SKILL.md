---
name: lesson-plan-writing
description: Writes a PNG lesson plan, for whichever grade and subject the request specifies, from a matched curriculum record. Enforces grade, subject, topic, and curriculum fidelity (no invented benchmark codes, no substituted grade/subject/topic). Use when generating the Lesson Plan stage of the PNG classroom resource pipeline.
---

# Lesson Plan Writing

You are writing a lesson plan: a teaching resource a teacher uses to prepare and
deliver a lesson in a PNG (Papua New Guinea) classroom. You write for PNG teachers generally, across any type of school. The grade and subject are not fixed - they are
given to you as data in this request (in the teacher's selection and/or the
matched curriculum record). Never assume a specific grade or subject; always use
the ones provided.

## Grade, subject, and topic fidelity

The teacher's request already resolved a grade, subject, and topic for this
lesson (from the curriculum match or the teacher's own selection, given to you in
this request). Build the entire lesson around exactly those - even if the topic
seems unusual for the stated subject - and never substitute a different grade,
subject, or topic of your own choosing.

## Curriculum fidelity

The curriculum match you were given has a `match_status` of `exact`, `suggested`,
or `custom`:

- **`exact`**: An official curriculum record exists. Use its fields (strand, unit,
  topic, benchmark_code, benchmark, content_standard_code, content_standard,
  learning_objectives) as the only source for those facts. Do not invent or alter
  a benchmark code, content standard, strand, unit, topic, or learning objective.
  - The "## Benchmark" section must start with the literal benchmark code (e.g.
    "9.3.3.3 - Apply and interpret...") - never give only the benchmark's
    description without its code.
  - The "## Content Standard" section must start with the literal content
    standard code (e.g. "CS1 - Students will be able to...") the same way.
- **`suggested`** or **`custom`**: There is no official curriculum record. Say so
  plainly at the top of both the "## Benchmark" and "## Content Standard"
  sections (e.g. "Custom topic - not directly matched to the official PNG
  curriculum") and do not fabricate a benchmark code or content standard code.

## Output format

Before writing, load `assets/template.md` from this skill via `load_skill_resource`
- it has the exact heading structure your response must follow. Do not write
your response until you have loaded it.
