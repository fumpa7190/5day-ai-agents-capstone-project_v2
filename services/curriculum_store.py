"""Loads the prepared PNG Grade 9 Mathematics curriculum files and answers
selection/matching queries against them.

This is the only place that touches the curriculum JSON/JSONL files - per the
spec, those files are the source of truth and nothing else (no LLM, no
network) is allowed to invent or alter curriculum data.
"""

import difflib
import json
import logging
from pathlib import Path
from typing import Optional

from schemas.curriculum import CurriculumMatch, MatchSuggestion

logger = logging.getLogger("orchestrator.curriculum_store")

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "curriculum" / "png" / "grade_9"

FUZZY_CUTOFF = 0.45
MAX_SUGGESTIONS = 3


def _load_json(name: str):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(name: str) -> list[dict]:
    rows = []
    path = DATA_DIR / name
    if not path.exists():
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class CurriculumStore:
    def __init__(self):
        self.records: list[dict] = _load_json("curriculum_records.json")
        self.indexes: dict = _load_json("indexes.json")
        self.selection_options: list[dict] = _load_json("selection_options.json")
        self.chunks: list[dict] = _load_jsonl("chunks.jsonl")
        self._by_id = {r["id"]: r for r in self.records}

    def get_selection_tree(self) -> dict:
        return self.indexes.get("selection_tree", {})

    def get_record(self, record_id: str) -> Optional[dict]:
        return self._by_id.get(record_id)

    def get_chunks(self, record_id: str) -> list[dict]:
        return [c for c in self.chunks if c.get("record_id") == record_id]

    def _topics_for(self, grade: int, subject: str) -> list[dict]:
        return [
            r
            for r in self.records
            if r.get("grade") == grade and r.get("subject", "").lower() == subject.lower()
        ]

    def match_selection(
        self,
        grade: int,
        subject: str,
        strand: Optional[str] = None,
        unit: Optional[str] = None,
        topic: Optional[str] = None,
        manual_topic: Optional[str] = None,
        force_custom: bool = False,
    ) -> CurriculumMatch:
        """Resolves a teacher's selection (dropdowns or manual entry) to a
        curriculum record. Dropdown `topic` is expected to already be an
        official topic name, so it is matched directly; `manual_topic` goes
        through exact-then-fuzzy matching with a `custom` fallback.

        `force_custom` skips the fuzzy-suggestion step for `manual_topic` -
        used once a teacher has already declined a suggested match, so the
        same manual topic doesn't just re-suggest the same thing again.
        """
        by_topic: dict = self.indexes.get("by_topic", {})

        if topic:
            record_id = by_topic.get(topic.strip().lower())
            if record_id:
                logger.info("curriculum_match: exact dropdown match -> %s", record_id)
                return CurriculumMatch(
                    match_status="exact",
                    record_id=record_id,
                    curriculum_record=self.get_record(record_id),
                )
            logger.warning("curriculum_match: dropdown topic '%s' not found in index", topic)

        if manual_topic and force_custom:
            logger.info("curriculum_match: manual topic '%s' forced custom by teacher", manual_topic)
            return CurriculumMatch(
                match_status="custom",
                warnings=[
                    f"'{manual_topic}' was confirmed by the teacher as a custom topic, not "
                    "directly matched to the extracted official curriculum."
                ],
            )

        if manual_topic:
            return self._match_manual_topic(grade, subject, manual_topic)

        logger.warning("curriculum_match: no topic or manual_topic provided")
        return CurriculumMatch(
            match_status="custom",
            warnings=["No topic or manual topic was provided."],
        )

    def _match_manual_topic(self, grade: int, subject: str, manual_topic: str) -> CurriculumMatch:
        by_topic: dict = self.indexes.get("by_topic", {})
        normalized = manual_topic.strip().lower()

        record_id = by_topic.get(normalized)
        if record_id:
            logger.info("curriculum_match: manual topic '%s' matched exactly -> %s", manual_topic, record_id)
            return CurriculumMatch(
                match_status="exact",
                record_id=record_id,
                curriculum_record=self.get_record(record_id),
                warnings=["Manual topic matched an official curriculum topic exactly."],
            )

        candidates = self._topics_for(grade, subject)
        topic_names = [r["topic"] for r in candidates]
        close = difflib.get_close_matches(
            manual_topic, topic_names, n=MAX_SUGGESTIONS, cutoff=FUZZY_CUTOFF
        )
        if close:
            seen_ids = set()
            suggestions = []
            for name in close:
                record = next(r for r in candidates if r["topic"] == name)
                if record["id"] in seen_ids:
                    continue
                seen_ids.add(record["id"])
                score = difflib.SequenceMatcher(None, normalized, name.lower()).ratio()
                suggestions.append(
                    MatchSuggestion(
                        record_id=record["id"],
                        topic=record["topic"],
                        strand=record["strand"],
                        unit=record["unit"],
                        benchmark_code=record["benchmark_code"],
                        score=round(score, 3),
                    )
                )
            logger.info(
                "curriculum_match: manual topic '%s' -> %d suggestion(s)", manual_topic, len(suggestions)
            )
            return CurriculumMatch(
                match_status="suggested",
                suggestions=suggestions,
                warnings=[
                    f"'{manual_topic}' did not exactly match an official curriculum topic. "
                    "Closest matches are suggested below."
                ],
            )

        logger.info("curriculum_match: manual topic '%s' -> custom (no close match)", manual_topic)
        return CurriculumMatch(
            match_status="custom",
            warnings=[
                f"'{manual_topic}' does not match any official PNG Grade {grade} {subject} "
                "curriculum topic. This will be treated as a custom topic, not directly "
                "matched to the extracted official curriculum."
            ],
        )

    def confirm_suggestion(self, record_id: str) -> CurriculumMatch:
        """Builds an exact CurriculumMatch once the teacher confirms a suggested match."""
        record = self.get_record(record_id)
        if record is None:
            return CurriculumMatch(
                match_status="custom",
                warnings=[f"Suggested record '{record_id}' could not be found."],
            )
        return CurriculumMatch(match_status="exact", record_id=record_id, curriculum_record=record)


_store: Optional[CurriculumStore] = None


def get_store() -> CurriculumStore:
    global _store
    if _store is None:
        _store = CurriculumStore()
    return _store
