"""Deterministic content-safety guardrail (spec guardrail #6: "Do not
generate harmful, discriminatory, or inappropriate classroom content").

Checked before a teacher-supplied manual topic ever reaches the model -
not a prompt instruction, so it can't be argued or jailbroken around the
way a prompt-only rule could. Deliberately a small, explicit pattern list
rather than a model-based classifier: the point is the code-level
enforcement pattern (block before the model ever sees it), which matters
more for an MVP than classifier coverage.
"""

import re

_DISALLOWED_PATTERNS = [
    r"\bsuicide\b",
    r"\bself[\s-]?harm\b",
    r"\bkill (myself|yourself|himself|herself|themselves)\b",
    r"\bweapon\b",
    r"\bbomb\b",
    r"\bexplosive\b",
    r"\bdrugs?\b",
    r"\bcocaine\b",
    r"\bheroin\b",
    r"\bporn\w*\b",
    r"\bsex\w*\b",
    r"\bracis\w*\b",
    r"\bnazis?\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _DISALLOWED_PATTERNS]


class UnsafeTopicError(ValueError):
    """Raised when a manually entered topic matches a disallowed content category."""


def check_topic_safety(text: str) -> None:
    """Raises `UnsafeTopicError` if `text` matches a disallowed category.

    Called before curriculum matching or any model call, so a disallowed
    topic never reaches the LLM at all - the same "block before the model
    sees it" pattern as a `before_model_callback`, just applied at the
    point a manual topic is first captured.
    """
    for pattern in _COMPILED:
        if pattern.search(text):
            raise UnsafeTopicError(
                "This topic isn't appropriate for a classroom resource generator."
            )
