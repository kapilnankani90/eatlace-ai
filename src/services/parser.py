"""Parse LLM JSON responses into Recommendation objects."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from src.models.recommendation import Recommendation
from src.models.restaurant import RestaurantRecord

FALLBACK_EXPLANATION = (
    "Ranked by rating and your filters. "
    "AI explanations are temporarily unavailable."
)


@dataclass
class ParseResult:
    recommendations: list[Recommendation]
    summary: str | None = None


class LLMResponseParser:
    """Parse and validate LLM output; merge with dataset records."""

    def parse(
        self,
        raw: str,
        candidates: list[RestaurantRecord],
        *,
        top_k: int,
    ) -> ParseResult:
        payload = self._load_json(raw)
        summary = payload.get("summary")
        if summary is not None:
            summary = str(summary).strip() or None

        items = payload.get("recommendations")
        if not isinstance(items, list):
            raise ValueError("Missing or invalid 'recommendations' array.")

        by_name = self._index_candidates(candidates)
        recommendations: list[Recommendation] = []
        seen_ids: set[str] = set()

        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("restaurant_name")
            if not name or not str(name).strip():
                continue
            record = self._match_record(str(name).strip(), by_name, candidates)
            if record is None or record.id in seen_ids:
                continue

            explanation = item.get("explanation")
            if not explanation or not str(explanation).strip():
                explanation = (
                    "Matches your preferences based on location, cuisine, and rating."
                )

            rank_raw = item.get("rank", len(recommendations) + 1)
            try:
                rank = int(rank_raw)
            except (TypeError, ValueError):
                rank = len(recommendations) + 1

            recommendations.append(
                Recommendation(
                    rank=rank,
                    restaurant=record,
                    explanation=str(explanation).strip(),
                )
            )
            seen_ids.add(record.id)
            if len(recommendations) >= top_k:
                break

        if not recommendations:
            raise ValueError("No valid recommendations after parsing.")

        recommendations.sort(key=lambda r: r.rank)
        recommendations = [
            Recommendation(
                rank=i,
                restaurant=rec.restaurant,
                explanation=rec.explanation,
            )
            for i, rec in enumerate(recommendations, start=1)
        ]

        return ParseResult(recommendations=recommendations, summary=summary)

    @staticmethod
    def build_fallback(
        candidates: list[RestaurantRecord],
        top_k: int,
    ) -> ParseResult:
        sorted_records = sorted(
            candidates,
            key=lambda r: (-r.rating, r.name.lower()),
        )[:top_k]
        recommendations = [
            Recommendation(
                rank=i,
                restaurant=record,
                explanation=FALLBACK_EXPLANATION,
            )
            for i, record in enumerate(sorted_records, start=1)
        ]
        return ParseResult(recommendations=recommendations, summary=None)

    def _load_json(self, raw: str) -> dict:
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence:
            text = fence.group(1).strip()
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("LLM response must be a JSON object.")
        return data

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r"[^\w\s]", "", name.lower()).strip()

    def _index_candidates(
        self, candidates: list[RestaurantRecord]
    ) -> dict[str, RestaurantRecord]:
        index: dict[str, RestaurantRecord] = {}
        for record in candidates:
            index[record.name] = record
            index[self._normalize_name(record.name)] = record
        return index

    def _match_record(
        self,
        name: str,
        by_name: dict[str, RestaurantRecord],
        candidates: list[RestaurantRecord],
    ) -> RestaurantRecord | None:
        if name in by_name:
            return by_name[name]
        normalized = self._normalize_name(name)
        if normalized in by_name:
            return by_name[normalized]

        for record in candidates:
            if self._normalize_name(record.name) == normalized:
                return record
            if normalized and normalized in self._normalize_name(record.name):
                return record
        return None
