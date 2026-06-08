"""Integration tests for RecommendationOrchestrator."""

import json

import pytest

from src.data.cache import DataCache
from src.models.preferences import Budget, UserPreferences
from src.models.restaurant import RestaurantRecord
from src.services.llm_client import MockLLMClient
from src.services.orchestrator import RecommendationOrchestrator


def _record(name: str, location: str, cuisines: list[str], rating: float, cost: float):
    return RestaurantRecord(
        id=name,
        name=name,
        location=location,
        cuisines=cuisines,
        rating=rating,
        estimated_cost=cost,
        metadata={"listed_in(city)": "Bangalore", "votes": 10},
    )


SAMPLE_RECORDS = [
    _record("Alpha Bistro", "Indiranagar", ["Italian"], 4.6, 500.0),
    _record("Beta Kitchen", "Koramangala", ["Chinese"], 4.0, 400.0),
    _record("Gamma Cafe", "Indiranagar", ["Cafe"], 3.5, 200.0),
]

MOCK_LLM_JSON = json.dumps(
    {
        "summary": "Solid picks in Bangalore.",
        "recommendations": [
            {
                "rank": 1,
                "restaurant_name": "Alpha Bistro",
                "explanation": "Great Italian fit.",
            }
        ],
    }
)


@pytest.fixture
def loaded_cache() -> DataCache:
    cache = DataCache()
    cache.set_records(SAMPLE_RECORDS, cost_percentile_33=350.0, cost_percentile_66=550.0)
    return cache


def test_orchestrator_full_pipeline(loaded_cache):
    mock_llm = MockLLMClient(MOCK_LLM_JSON)
    orchestrator = RecommendationOrchestrator(cache=loaded_cache, llm_client=mock_llm)
    prefs = UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="Italian",
    )

    result = orchestrator.recommend(prefs, require_groq_key=False)

    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant.name == "Alpha Bistro"
    assert result.summary == "Solid picks in Bangalore."
    assert not result.used_fallback
    assert len(mock_llm.calls) == 1


def test_orchestrator_skips_llm_when_no_candidates(loaded_cache):
    mock_llm = MockLLMClient(MOCK_LLM_JSON)
    orchestrator = RecommendationOrchestrator(cache=loaded_cache, llm_client=mock_llm)
    prefs = UserPreferences(
        location="Nonexistent",
        budget=Budget.LOW,
    )

    result = orchestrator.recommend(prefs, require_groq_key=False)

    assert result.is_empty
    assert len(mock_llm.calls) == 0


def test_orchestrator_fallback_on_llm_failure(loaded_cache):
    from src.services.llm_client import LLMError

    class FailingClient(MockLLMClient):
        def complete(self, system: str, user: str) -> str:
            raise LLMError("Groq down")

    orchestrator = RecommendationOrchestrator(
        cache=loaded_cache,
        llm_client=FailingClient(""),
    )
    prefs = UserPreferences(location="Bangalore", budget=Budget.MEDIUM)

    result = orchestrator.recommend(prefs, require_groq_key=False)

    assert result.used_fallback
    assert len(result.recommendations) >= 1


def test_orchestrator_requires_groq_key_by_default(loaded_cache, monkeypatch):
    monkeypatch.setattr("src.config.GROQ_API_KEY", None)
    orchestrator = RecommendationOrchestrator(cache=loaded_cache)
    prefs = UserPreferences(location="Bangalore", budget=Budget.MEDIUM)

    from src.services.llm_client import LLMError

    with pytest.raises(LLMError, match="GROQ_API_KEY"):
        orchestrator.recommend(prefs, require_groq_key=True)
