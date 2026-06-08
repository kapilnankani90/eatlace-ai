"""Tests for RecommendationEngine with mocked LLM."""

import json

from src.models.preferences import Budget, UserPreferences
from src.models.restaurant import RestaurantRecord
from src.services.llm_client import LLMError, MockLLMClient
from src.services.recommendation_engine import RecommendationEngine


def _candidate(name: str, rating: float) -> RestaurantRecord:
    return RestaurantRecord(
        id=name,
        name=name,
        location="Koramangala",
        cuisines=["Italian"],
        rating=rating,
        estimated_cost=500.0,
    )


MOCK_LLM_JSON = json.dumps(
    {
        "summary": "Enjoy these picks.",
        "recommendations": [
            {
                "rank": 1,
                "restaurant_name": "Top Pick",
                "explanation": "Best match for Italian lovers.",
            }
        ],
    }
)


def test_recommend_with_mock_llm():
    prefs = UserPreferences(location="Bangalore", budget=Budget.MEDIUM, cuisine="Italian")
    candidates = [_candidate("Top Pick", 4.8), _candidate("Other", 4.0)]

    engine = RecommendationEngine(llm_client=MockLLMClient(MOCK_LLM_JSON))
    result = engine.recommend(prefs, candidates, top_k=1)

    assert not result.used_fallback
    assert result.summary == "Enjoy these picks."
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant.name == "Top Pick"
    assert "Italian" in result.recommendations[0].explanation


def test_recommend_empty_candidates():
    prefs = UserPreferences(location="Bangalore", budget=Budget.LOW)
    result = RecommendationEngine(llm_client=MockLLMClient(MOCK_LLM_JSON)).recommend(
        prefs, []
    )
    assert result.is_empty


def test_fallback_on_llm_error():
    class FailingClient(MockLLMClient):
        def complete(self, system: str, user: str) -> str:
            raise LLMError("API down")

    prefs = UserPreferences(location="Bangalore", budget=Budget.MEDIUM)
    candidates = [_candidate("A", 4.5), _candidate("B", 4.0)]

    result = RecommendationEngine(llm_client=FailingClient("")).recommend(
        prefs, candidates, top_k=2
    )

    assert result.used_fallback
    assert len(result.recommendations) == 2
    assert result.recommendations[0].restaurant.name == "A"


def test_fallback_on_invalid_json():
    prefs = UserPreferences(location="Bangalore", budget=Budget.MEDIUM)
    candidates = [_candidate("A", 4.5)]

    client = MockLLMClient("not json at all")
    result = RecommendationEngine(llm_client=client).recommend(
        prefs, candidates, top_k=1
    )

    assert result.used_fallback
    assert len(client.calls) == 2
