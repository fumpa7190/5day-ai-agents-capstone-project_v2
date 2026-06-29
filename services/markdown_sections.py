"""Parses an LLM agent's Markdown response into one of the section schemas.

Agents are prompted (see /prompts) to head each part of their answer with a
Markdown heading matching a schema field name (e.g. "## Teacher Activities"
for `teacher_activities`). This keeps generation robust against a small local
model that can write good Markdown prose far more reliably than deeply
nested, schema-exact JSON - see plan decision 2 in
specs/png-classroom-agent-workflow.md's implementation plan.
"""

import re
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_HEADING_RE = re.compile(r"^#{1,3}\s+(.+?)\s*$", flags=re.MULTILINE)


def _normalize(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", heading.strip().lower()).strip("_")


def parse(text: str, schema_cls: type[T]) -> T:
    """Splits `text` on Markdown headings into `schema_cls`'s fields.

    Headings are matched to field names by normalizing both to snake_case, so
    "## Teacher Activities" fills `teacher_activities`. Unrecognized headings
    are ignored (not dropped - they remain part of `raw_markdown`, which
    always holds the full original text as a fallback).

    A heading that appears more than once (e.g. the Assessment agent in
    "full_pack" mode naturally writes a "## Marking Guide" after each of
    Quick Quiz/Short Test/Assignment, rather than one combined one at the
    end) has its occurrences concatenated, not overwritten - the first
    observed behavior here was a later, genuinely empty occurrence silently
    wiping out two earlier, populated ones.
    """
    field_names = {name for name in schema_cls.model_fields if name != "raw_markdown"}
    sections: dict[str, list[str]] = {}

    headings = list(_HEADING_RE.finditer(text))
    for idx, match in enumerate(headings):
        key = _normalize(match.group(1))
        if key not in field_names:
            continue
        start = match.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        content = text[start:end].strip()
        if content:
            sections.setdefault(key, []).append(content)

    joined = {key: "\n\n".join(parts) for key, parts in sections.items()}
    return schema_cls(**joined, raw_markdown=text.strip())
