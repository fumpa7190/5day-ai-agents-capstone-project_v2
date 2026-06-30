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
# A LaTeX-style math span: two '$' on the same line with no '$' between them.
# Matched and stripped *before* the currency check below, so a digit right
# after the opening '$' (e.g. "$3(2x + 3)$") isn't mistaken for a price.
_PAIRED_DOLLAR_RE = re.compile(r"\$([^$\n]+)\$")
_CURRENCY_DOLLAR_RE = re.compile(r"\$(\d)")


def _normalize(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", heading.strip().lower()).strip("_")


def sanitize_dollar_signs(text: str) -> str:
    """Deterministically repairs '$' usage a small local model sometimes
    still writes despite png-classroom-conventions' rule against it: PNG
    currency must use 'K' (Kina), and LaTeX math delimiters ('$...$') aren't
    supported by this app's Markdown-to-Word/PDF pipeline.

    Order matters: a paired '$...$' span is assumed to be a LaTeX math
    delimiter and is unwrapped first, keeping its (already plain-text)
    content (e.g. "$3(2x + 3)$" -> "3(2x + 3)") - this must run before the
    currency check, otherwise the digit right after the opening '$' would be
    misread as a price. Any '$<digit>' left after that is an un-converted
    currency amount and becomes 'K<digit>' (e.g. "$5" -> "K5"). Any
    remaining stray '$' is simply dropped.

    This runs before parsing, the same enforce-in-code approach as
    `orchestrator.pipeline._backfill_benchmark_and_standard`, rather than
    just flagging it after the fact (see services/review.py's
    `_check_no_dollar_signs`, which stays as a safety net). Note this is a
    heuristic, not a parser: two unrelated currency amounts on the same
    line with no other '$' between them (e.g. "$5 today and $10 tomorrow")
    will be misread as one paired span and lose their 'K' prefixes - an
    accepted tradeoff favoring the far more common single-expression case.
    """
    text = _PAIRED_DOLLAR_RE.sub(r"\1", text)
    text = _CURRENCY_DOLLAR_RE.sub(r"K\1", text)
    return text.replace("$", "")


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
