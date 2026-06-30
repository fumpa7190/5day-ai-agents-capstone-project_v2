# Title

Lesson Plans Without the Cloud: A Local Multi-Agent Teaching Assistant for Rural Papua New Guinea

# Introduction

Papua New Guinea is an island nation in the southwestern Pacific, located just north of Australia. It is home to approximately 10–11 million people, most of whom live in rural and remote communities where reliable electricity and internet access remain limited. To support teachers in these underserved areas, this project delivers a teacher-guided, curriculum-grounded AI system that runs entirely on a lightweight local language model. Designed to operate on standard classroom hardware today, it also lays the foundation for an offline, solar-powered future.

# Writeup

## The Problem

Preparing high-quality lesson plans, classroom activities, and assessments is time-consuming for any teacher. In rural Papua New Guinea, the challenge is even greater. Many schools have limited access to computers, unreliable internet connectivity, and constrained budgets, making cloud-based AI solutions impractical.

Most modern AI tools assume users have continuous internet access, paid API subscriptions, and powerful hardware. For many teachers in rural Papua New Guinea, these assumptions simply do not hold.

This project was designed around the opposite assumption: build for the hardware teachers already have, not the hardware we wish they had.

## The Proposed Solution

The PNG Classroom Resource Generator is a lightweight Streamlit application powered entirely by a local Gemma model. Instead of generating an entire lesson pack in a single prompt, it guides teachers through the same workflow they naturally follow when preparing a lesson.

The application uses a teacher-guided multi-agent pipeline, where each stage builds upon the previous one:

1. Select a curriculum topic and generate a lesson plan aligned with the official PNG curriculum.
2. Review and approve the lesson plan before generating classroom activities and teacher notes.
3. Review again before generating assessments, quizzes, assignments, and a marking guide.

Each step is presented to the teacher before the next begins, ensuring that the teacher remains in control throughout the entire process. The completed lesson pack can then be exported as an editable Microsoft Word document or a formatted PDF, ready for classroom use or further refinement.

## Why Local? Why Lightweight?

Every stage of the pipeline runs locally using Gemma 4 E2B IT QAT, a lightweight 4-billion-parameter quantized model served through LM Studio.

This model was deliberately chosen because it offers an excellent balance between capability and accessibility. It is small enough to run on ordinary desktops and aging laptops while still producing reliable structured outputs for educational content generation.

Running the model locally also means:

- No internet connection is required after installation.
- No API keys or subscription fees.
- No per-request usage costs.
- Greater privacy, as curriculum data and teacher inputs remain on the local device.

For schools with limited connectivity, these characteristics are essential rather than optional.

## From Topic to Printed Lesson: The Agent and Tool Flow

```
 Teacher picks topic
         |
         v
 1. Curriculum Match              (deterministic, no model call)
         |
         v
 2. Lesson Plan Agent             (skills: conventions + lesson-plan-writing)
         |  reviewed -> shown to teacher
         v
 3. Activities Agent -> Teacher Notes Agent      (ADK SequentialAgent, own skills)
         |  reviewed -> shown to teacher
         v
 4. Assessment Agent              (skill: assessment-writing)
         |  reviewed -> shown to teacher
         v
 5. Export -> Word (.docx) / PDF
```

1. **Curriculum match (no model call).** The teacher's selection - or a manually typed topic, checked first against a content-safety filter - is matched against the real PNG curriculum records in `services/curriculum_store.py`. Nothing goes to the model until this returns.
2. **Lesson Plan agent.** An ADK `LlmAgent` loads two skills through a `SkillToolset` tool - `png-classroom-conventions` and `lesson-plan-writing` - then writes the lesson plan as structured Markdown, grounded in the matched curriculum record. A deterministic review pass (`services/review.py`) checks it for missing fields and unavailable resources before it's shown to the teacher.
3. **Activities and Teacher Notes agents.** Once the teacher approves the plan, ADK's `SequentialAgent` runs two more `LlmAgent`s one after another - each with their own scoped skill, building directly on the lesson plan just produced. Reviewed and shown the same way.
4. **Assessment agent.** A final `LlmAgent`, loaded with the `assessment-writing` skill, generates the quiz, test, assignment, and marking guide - built on the lesson plan *and* the activities/notes from the step before, so the assessment matches what was actually taught. Reviewed and shown the same way.
5. **Export.** The approved sections are assembled into one Markdown document, then converted to HTML and rendered into a downloadable Word (`.docx`) or PDF file - ready to print or revise, no further model calls involved.

## Capstone Concepts Demonstrated

- **Multi-agent system:** four ADK `LlmAgent`s, each with one job, coordinating through explicitly shared state - not a single model call dressed up as "agentic."
- **Sequential agent workflow:** the Activities and Teacher Notes agents are chained with ADK's `SequentialAgent`, so the second agent always runs after - and builds on - the first, rather than the two competing or running independently.
- **Agent Skills:** each agent's procedural knowledge lives in a versioned `SKILL.md`, loaded at runtime through a `SkillToolset` scoped to only the skills that agent needs.
- **Security / guardrails:** curriculum facts are isolated from the model entirely, a content-safety filter blocks disallowed manual topics before any model call runs, and a deterministic review pass catches what the model still gets wrong.
- **Deployability:** a one-file launcher, no command line needed.

## Looking Ahead

While this prototype currently runs on a standard laptop, its long-term vision is to bring AI-powered teaching assistance to even the most remote classrooms through lightweight local language models running on low-power, solar-powered devices.

Every design decision—from the lightweight local model to the teacher-guided workflow—was driven by one question: Would this work for a teacher with no internet and an aging laptop? By reducing the time needed to prepare curriculum-aligned lesson plans, activities, and assessments, teachers can spend more time teaching and less time creating resources.

Ultimately, this project demonstrates how practical, local AI can empower teachers wherever they teach, making quality educational support accessible regardless of internet connectivity, hardware, or location.
