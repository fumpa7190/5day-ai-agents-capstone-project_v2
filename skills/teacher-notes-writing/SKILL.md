---
name: teacher-notes-writing
description: Writes teacher-facing notes (key concepts, a simple explanation, worked examples, common student mistakes, teaching tips, a local context example) so a teacher can confidently explain a topic, for whichever grade and subject the request specifies. Use when generating the Teacher Notes stage of the PNG classroom resource pipeline.
---

# Teacher Notes Writing

You are writing teacher notes: a teaching resource a teacher uses to explain a
topic confidently in a PNG (Papua New Guinea) classroom - including when the
teacher themselves is less familiar with the topic. You write for PNG teachers generally, across any type of school. The grade and subject are not fixed - they are
given to you as data in this request, in the lesson plan already generated for
this lesson. Never assume a specific grade or subject.

## Audience and depth

- These notes are for the **teacher**, not the students - keep them clear and
  classroom-ready, but you can write at a slightly higher level than you would
  for a student-facing resource.
- Avoid overcomplicating the subject matter. Explain it the way you would to a
  colleague who is preparing to teach this topic for the first time.
- Include a step-by-step worked example or walkthrough of how to work through
  the topic, not just the final answer or outcome.

## Output format

Before writing, load `assets/template.md` from this skill via `load_skill_resource`
- it has the exact heading structure your response must follow. Do not write
your response until you have loaded it.
