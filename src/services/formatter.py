"""Format recommendation results for CLI and other outputs."""

from __future__ import annotations

import json
from typing import Any

from src.models.recommendation import Recommendation, RecommendationResult


class ResultFormatter:
    """Human-readable and structured formatters for recommendation output."""

    def format_cli(self, result: RecommendationResult) -> str:
        lines: list[str] = []

        for message in result.filter_messages:
            lines.append(f"Note: {message}")

        if not result.recommendations:
            if not any("No restaurants found" in m for m in result.filter_messages):
                lines.append("No candidates to recommend.")
            return "\n".join(lines)

        if result.used_fallback:
            lines.append(
                "Note: Using rating-based fallback "
                "(Groq unavailable or invalid response)."
            )

        if result.summary:
            lines.append(f"\nSummary: {result.summary}\n")

        lines.append(f"Top {len(result.recommendations)} recommendations:")
        for rec in result.recommendations:
            lines.append(self._format_recommendation_block(rec))

        return "\n".join(lines)

    def format_json(self, result: RecommendationResult) -> str:
        return json.dumps(result.to_dict(), indent=2, default=str)

    def _format_recommendation_block(self, rec: Recommendation) -> str:
        r = rec.restaurant
        cuisines = ", ".join(r.cuisines) if r.cuisines else "N/A"
        cost = r.estimated_cost if r.estimated_cost is not None else "N/A"
        return (
            f"\n#{rec.rank} {r.name}\n"
            f"  Location: {r.location}\n"
            f"  Cuisine: {cuisines}\n"
            f"  Rating: {r.rating:.1f}\n"
            f"  Cost for two: {cost}\n"
            f"  Why: {rec.explanation}"
        )

    def to_display_dict(self, result: RecommendationResult) -> dict[str, Any]:
        """Structured payload for UI layers (Phase 5)."""
        return {
            "summary": result.summary,
            "used_fallback": result.used_fallback,
            "filter_messages": result.filter_messages,
            "recommendations": [
                {
                    "rank": rec.rank,
                    "name": rec.restaurant.name,
                    "location": rec.restaurant.location,
                    "cuisines": rec.restaurant.cuisines,
                    "rating": rec.restaurant.rating,
                    "estimated_cost": rec.restaurant.estimated_cost,
                    "explanation": rec.explanation,
                }
                for rec in result.recommendations
            ],
        }
