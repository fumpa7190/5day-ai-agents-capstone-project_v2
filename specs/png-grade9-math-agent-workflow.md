# SPEC: PNG Classroom AI Resource Generator — Multi-Agent Workflow

## 1. Project Goal

Build a lightweight AI-assisted school resource generator for PNG teachers, for
whichever grade and subject the teacher selects (see the Main Teacher Interface
Flow, section 3). Grade and subject are parameters of the system - not a fixed
scope baked into the agents, their prompts, or their skills.

**Current data scope:** the curriculum data actually prepared and loaded so far
covers only:

* Country: Papua New Guinea
* Curriculum: Standards-Based Curriculum
* Grade: 9
* Subject: Mathematics

This is a data-loading limitation, not an architectural one - adding another
grade or subject means preparing its curriculum files in the same format (see
section 2), not changing any agent, prompt, or skill.

Teachers select curriculum options from prepared JSON files, then the system generates:

* Lesson Plan
* Lesson Activities
* Teacher Notes
* Quiz / Test
* Assignment
* Full Lesson Pack

The app must run lightly on a standard computer and should avoid heavy vector databases for the MVP.

---

## 2. Source of Truth

The app must use prepared curriculum files as the source of truth.

Expected files:

```text
/data/curriculum/png/math/grade_9/
  curriculum_records.json
  syllabus_records.json
  selection_options.json
  indexes.json
  chunks.jsonl
  manifest.json
```

The AI must not invent syllabus standards, benchmark codes, strands, units, topics, or learning objectives.

If a teacher enters a manual topic that does not match the prepared curriculum, mark it as a custom topic and show that it is not directly matched to the official extracted curriculum.

---

## 3. Main Teacher Interface Flow

The teacher should select:

```text
Grade
→ Subject
→ Strand
→ Unit
→ Topic
→ Learning Objective / Benchmark
→ Resource Type
→ Classroom Context
```

Classroom context fields:

```text
Lesson duration
Class ability
Resources available
Language level
Optional uploaded resources
```

Example:

```json
{
  "grade": 9,
  "subject": "Mathematics",
  "strand": "Patterns and Algebra",
  "unit": "Linear Relations",
  "topic": "Linear Relationships",
  "resource_type": "Full Lesson Pack",
  "class_context": {
    "duration": "40 minutes",
    "ability": "Mixed",
    "resources": ["Blackboard only", "Exercise books"],
    "language_level": "Simple English"
  }
}
```

---

## 4. Multi-Agent Workflow

Use an orchestrated multi-agent workflow. Resource-generation agents run
**sequentially, never in parallel** - dispatching them concurrently against a
single local LLM instance (LM Studio) exceeds its shared context budget; there
is no real concurrency benefit against a single local model instance anyway.

```text
Teacher Selection
      ↓
Curriculum Matching (deterministic, no LLM)
      ↓
Lesson Planning Agent
      ↓
Sequential Resource Generation
      ├── Activities Agent
      └── Teacher Notes Agent
      ↓
Assessment Agent
      ↓
Review and Alignment (deterministic, no LLM)
      ↓
Final Output Package
```

Note: a Worksheet Agent existed in an earlier iteration of this project and may
return later, but it is deferred from the current pipeline - not forgotten. Don't
add it back to this diagram until it's actually wired into the orchestrator.

---

## 5. Agent Responsibilities

### 5.1 Curriculum Matching Agent

Purpose:

Find the correct curriculum record based on teacher selection or manual topic.

Inputs:

```json
{
  "grade": 9,
  "subject": "Mathematics",
  "strand": "...",
  "unit": "...",
  "topic": "...",
  "manual_topic": "optional"
}
```

Responsibilities:

* Load `selection_options.json`
* Load `indexes.json`
* Match selected topic to `curriculum_records.json`
* Return the full curriculum record
* If no exact match, suggest closest matches
* If still unmatched, return `custom_topic: true`

Output:

```json
{
  "match_status": "exact | suggested | custom",
  "record_id": "...",
  "curriculum_record": {},
  "warnings": []
}
```

---

### 5.2 Lesson Planning Agent

Purpose:

Generate a lesson plan from the selected curriculum record.

Must use:

* strand
* unit
* topic
* content standard
* benchmark code
* benchmark
* learning objectives
* classroom context

Must produce:

```text
Lesson title
Grade
Subject
Strand
Unit
Topic
Benchmark
Learning objectives
Prior knowledge
Materials
Introduction
Teacher activities
Student activities
Guided practice
Independent practice
Assessment for learning
Closure
Homework
Teacher reflection
```

Rules:

* Do not invent benchmark codes.
* Use simple language suitable for PNG teachers.
* Prefer low-resource classroom activities.
* Keep activities realistic for the lesson duration.

---

### 5.3 Activities Agent

Purpose:

Generate practical classroom activities.

Must produce:

```text
Starter activity
Main activity
Group activity
Individual practice
Extension activity
Support activity for struggling learners
```

Rules:

* Activities must align to the selected learning objectives.
* Prefer blackboard, exercise book, local examples, and low-resource methods.
* Avoid requiring internet unless teacher selected it as available.

---

### 5.4 Teacher Notes Agent

Purpose:

Generate notes the teacher can use to explain the topic.

Must produce:

```text
Key concepts
Simple explanation
Worked examples
Common student mistakes
Teaching tips
Local PNG context example where possible
```

Rules:

* Keep notes clear and classroom-ready.
* Avoid overcomplicating the subject matter - explain it the way you would to a
  colleague preparing to teach this for the first time.
* Include step-by-step worked examples.

---

### 5.5 Worksheet Agent

Purpose:

Generate student worksheet content.

Must produce:

```text
Student instructions
Example question
Practice questions
Challenge questions
Answer key
```

Rules:

* Questions must match the topic and learning objectives.
* Include mixed difficulty.
* Keep formatting printable.

---

### 5.6 Assessment Agent

Purpose:

Generate assessment items.

Must produce one or more:

```text
Quick quiz
Exit ticket
Short test
Assignment
Marking guide
Rubric where appropriate
```

Rules:

* Assessment must provide evidence that students met the learning objectives.
* Include answer key or marking guide.
* Use simple, measurable criteria.

---

### 5.7 Review and Alignment Agent

Purpose:

Check final output before showing it to the teacher.

Checklist:

```text
Does the output match the selected grade?
Does it match the subject?
Does it match the strand?
Does it match the unit and topic?
Does it use the correct benchmark code?
Does it align to the learning objectives?
Are activities realistic for the selected duration?
Are resources realistic for the selected classroom context?
Is the language level appropriate?
Are assessments linked to the objectives?
```

Output:

```json
{
  "alignment_status": "pass | needs_review",
  "issues": [],
  "suggested_fixes": [],
  "final_output": {}
}
```

---

## 6. Guardrails

The app must follow these rules:

1. Never invent official curriculum data.
2. Always generate from a structured curriculum record where possible.
3. If using a manual topic, clearly label it as custom.
4. Uploaded teacher resources are optional context, not the official source of truth.
5. Do not overwrite official syllabus data with uploaded content.
6. Do not generate harmful, discriminatory, or inappropriate classroom content.
7. Keep outputs suitable for school use.
8. Keep the teacher in control before saving, exporting, or sharing any generated material.

---

## 7. BDD Scenarios

### Scenario 1: Teacher selects an official topic

Given the teacher selects Grade 9 Mathematics
And selects a strand, unit, and topic from the prepared curriculum options
When the teacher clicks Generate Lesson Plan
Then the app retrieves the matching curriculum record
And the Lesson Planning Agent generates a lesson plan aligned to the benchmark and learning objectives
And the Review Agent checks the output before display

### Scenario 2: Teacher manually enters a topic

Given the teacher cannot find the topic in the dropdown
When the teacher enters a manual topic
Then the Curriculum Matching Agent searches for the closest matching curriculum records
And asks the teacher to confirm the closest match
If no match is confirmed
Then the topic is treated as a custom topic
And the generated output clearly states that it is not directly matched to the extracted official curriculum

### Scenario 3: Teacher requests a full lesson pack

Given the teacher selects a curriculum topic
And selects Full Lesson Pack
When generation starts
Then the Lesson Planning Agent creates the lesson plan
And the Activities Agent and Teacher Notes Agent generate their sections in sequence
And the Assessment Agent then generates its section, building on all of the above
And the Review Agent validates alignment
And the app returns one complete classroom-ready package

### Scenario 4: Low-resource classroom

Given the teacher selects “Blackboard only” as available resource
When the agents generate content
Then no activity should require internet, projector, printer, or calculator unless optional alternatives are provided

### Scenario 5: Review fails

Given the Review Agent detects that the assessment does not match the learning objectives
When the review fails
Then the app should regenerate or flag the assessment section
And the final output should not be marked as aligned until fixed

---

## 8. Coding Agent Instructions

Before writing code:

1. Read this spec.
2. Propose the folder structure.
3. Propose the data loading strategy.
4. Confirm the agent workflow.
5. Confirm the JSON schema for generated outputs.
6. Only then start implementation.

Implementation requirements:

* Keep the MVP lightweight.
* Use local JSON and JSONL files.
* Avoid adding a vector database for the MVP.
* Add tests for curriculum lookup.
* Add tests for manual topic fallback.
* Add tests for output schema validation.
* Add basic logging for each workflow step.
* Keep agent prompts separate from application logic.
* Do not hardcode curriculum records inside prompts.
* Load curriculum context from the prepared files.

Suggested folders:

```text
/app
  /data/curriculum/png/math/grade_9
  /agents
  /orchestrator
  /schemas
  /services
  /tests
  /prompts
  /docs
  /specs
```

---

## 9. Definition of Done

The MVP is complete when:

* Teachers can select grade/subject options from extracted curriculum data (today,
  that data covers Grade 9 Mathematics only - see section 1).
* The app can retrieve the correct curriculum record.
* The app can generate at least one lesson plan.
* The app can generate activities, notes, and assessment. (Worksheet is deferred
  - see section 4.)
* Manual topic fallback works.
* The Review Agent checks alignment.
* Outputs are structured and export-ready.
* Tests pass for curriculum lookup and generation workflow.
