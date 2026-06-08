"""LLM recommendation result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.restaurant import RestaurantRecord


@dataclass(frozen=True)
class Recommendation:
    """One ranked restaurant with dataset facts and AI explanation."""

    rank: int
    restaurant: RestaurantRecord
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "restaurant": self.restaurant.to_dict(),
            "explanation": self.explanation,
        }


@dataclass
class RecommendationResult:
    """Full outcome of the recommendation engine."""

    recommendations: list[Recommendation] = field(default_factory=list)
    summary: str | None = None
    used_fallback: bool = False
    filter_messages: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.recommendations) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "used_fallback": self.used_fallback,
            "filter_messages": self.filter_messages,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }
