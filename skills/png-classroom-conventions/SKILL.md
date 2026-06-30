---
name: png-classroom-conventions
description: General conventions for any PNG (Papua New Guinea) classroom resource - matching the resources actually available, mixed-ability differentiation, local context examples, and language level. Apply this skill alongside the skill specific to the resource type you are generating (lesson plan, activities, teacher notes, or assessment).
---

# PNG Classroom Conventions

These conventions apply to every PNG classroom resource you generate, regardless of
resource type. Apply them on top of - never instead of - the resource-type-specific
skill you also loaded for this task.

## 1. Only use what's actually available

Only assume a resource is available if it is explicitly listed in the `resources`
field of the classroom context you were given. Unless listed, do not require:

- Internet access
- A projector
- A printer
- A calculator

Default to blackboard/chalkboard, exercise books, and materials a PNG teacher could
plausibly find around the school or village (stones, bottle caps, sticks, leaves,
locally printed materials).

## 2. Local PNG context, when it fits naturally

Where an example would help (a worked problem, a scenario, an activity setup),
prefer a local PNG context: markets, gardens, fishing, local currency, village
distances, school events. If no PNG-specific example fits the topic naturally,
it is fine to use a neutral example rather than forcing one in.

**Currency:** PNG's currency is the Kina (with Toea as the subunit, 100 Toea =
1 Kina). Write amounts with the symbol **K**, not $ - e.g. "K5", "K2.50",
"K15.00", never "$5" or "$2.50". This applies to every currency amount you
write, not just the first one in a worked example.

## 3. Mixed-ability differentiation

PNG classrooms are commonly mixed-ability and sometimes multi-grade. Use the
classroom context's `ability` field: wherever the resource type has room for it,
give struggling learners an easier entry point into the same objective, and give
learners who finish early something that stretches them - do not write a single
difficulty level and call it done.

## 4. Language level and realism

- Use simple, clear language matching the classroom context's `language_level` -
  avoid unnecessarily technical phrasing.
- Keep every activity, explanation, or assessment item realistic for the stated
  lesson `duration`. Do not design something that could not plausibly happen in
  that time.

## 5. Write math in plain text, not LaTeX

Your response is rendered directly into a webpage, Word document, or PDF - none
of which understand LaTeX math notation. Never wrap expressions in `$...$` or
`$$...$$`, and never use LaTeX commands like `\frac`, `\div`, `\times`,
`\rightarrow`, or `\%`. Write the plain-text equivalent instead:

- Write "1/4" or "one quarter", not `$\frac{1}{4}$`.
- Write "6:9 simplified to 2:3", not `$6:9$` simplified to `$2:3$`.
- Write "25%", not `$25\%$`.
- Write "3 x 5 = 15", not `$3 \times 5 = 15$`.
- Write "3(2x + 3)", not `$3(2x + 3)$` - this applies to every algebraic
  expression, not just fractions, ratios, percentages, or multiplication.

If LaTeX would normally be the natural way to typeset something, the plain-text
form is what actually displays correctly here - LaTeX will only show up as
literal dollar signs and backslashes.
