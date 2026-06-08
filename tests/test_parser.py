"""Tests for LLM response parser."""

import json
import pytest

from src.models.restaurant import RestaurantRecord
from src.services.parser import FALLBACK_EXPLANATION, LLMResponseParser


def _candidate(name: str, rating: float = 4.0) -> RestaurantRecord:
    return RestaurantRecord(
        id=name,
        name=name,
        location="Area",
        cuisines=["Cafe"],
        rating=rating,
        estimated_cost=400.0,
    )


VALID_RESPONSE = json.dumps(
    {
        "summary": "Great options for your taste.",
        "recommendations": [
            {
                "rank": 1,
                "restaurant_name": "Alpha Bistro",
                "explanation": "Strong Italian menu and high rating.",
            },
            {
                "rank": 2,
                "restaurant_name": "Beta Kitchen",
                "explanation": "Fits your budget in Bangalore.",
            },
        ],
    }
)


class TestLLMResponseParser:
    def test_parse_valid_json(self):
        candidates = [_candidate("Alpha Bistro"), _candidate("Beta Kitchen")]
        result = LLMResponseParser().parse(VALID_RESPONSE, candidates, top_k=2)

        assert result.summary == "Great options for your taste."
        assert len(result.recommendations) == 2
        assert result.recommendations[0].restaurant.name == "Alpha Bistro"
        assert "Italian" in result.recommendations[0].explanation

    def test_parse_strips_markdown_fences(self):
        wrapped = f"```json\n{VALID_RESPONSE}\n```"
        candidates = [_candidate("Alpha Bistro"), _candidate("Beta Kitchen")]
        result = LLMResponseParser().parse(wrapped, candidates, top_k=2)
        assert len(result.recommendations) == 2

    def test_rejects_unknown_restaurant_name(self):
        raw = json.dumps(
            {
                "recommendations": [
                    {
                        "rank": 1,
                        "restaurant_name": "Fake Place",
                        "explanation": "Not in list.",
                    },
                    {
                        "rank": 2,
                        "restaurant_name": "Alpha Bistro",
                        "explanation": "Valid.",
                    },
                ]
            }
        )
        candidates = [_candidate("Alpha Bistro")]
        result = LLMResponseParser().parse(raw, candidates, top_k=2)
        assert len(result.recommendations) == 1
        assert result.recommendations[0].restaurant.name == "Alpha Bistro"

    def test_parse_fails_when_all_hallucinated(self):
        raw = json.dumps(
            {
                "recommendations": [
                    {
                        "rank": 1,
                        "restaurant_name": "Fake Place",
                        "explanation": "Nope.",
                    }
                ]
            }
        )
        with pytest.raises(ValueError):
            LLMResponseParser().parse(raw, [_candidate("Alpha Bistro")], top_k=1)

    def test_fallback_orders_by_rating(self):
        candidates = [
            _candidate("Low", rating=3.5),
            _candidate("High", rating=4.9),
        ]
        result = LLMResponseParser.build_fallback(candidates, top_k=2)
        assert result.recommendations[0].restaurant.name == "High"
        assert result.recommendations[0].explanation == FALLBACK_EXPLANATION

    def test_renumbers_ranks_sequentially(self):
        raw = json.dumps(
            {
                "recommendations": [
                    {"rank": 5, "restaurant_name": "B", "explanation": "Second."},
                    {"rank": 2, "restaurant_name": "A", "explanation": "First."},
                ]
            }
        )
        candidates = [_candidate("A"), _candidate("B")]
        result = LLMResponseParser().parse(raw, candidates, top_k=2)
        ranks = [r.rank for r in result.recommendations]
        assert ranks == [1, 2]
