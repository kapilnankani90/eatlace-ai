"""Tests for PromptBuilder."""

import json

from src.models.preferences import Budget, UserPreferences
from src.models.restaurant import RestaurantRecord
from src.services.prompt_builder import PromptBuilder


def _candidate(name: str) -> RestaurantRecord:
    return RestaurantRecord(
        id="1",
        name=name,
        location="Indiranagar",
        cuisines=["Italian"],
        rating=4.5,
        estimated_cost=600.0,
    )


def test_build_includes_preferences_and_candidates():
    prefs = UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )
    candidates = [_candidate("Trattoria"), _candidate("Pizza Hub")]

    system, user = PromptBuilder().build(prefs, candidates, top_k=2)

    assert "restaurant recommendation" in system.lower()
    assert "Bangalore" in user
    assert "Italian" in user
    assert "family-friendly" in user
    assert "Trattoria" in user
    assert "Pizza Hub" in user
    assert '"recommendations"' in user
    assert "top 2" in user.lower()


def test_strict_json_mode_adds_instruction():
    prefs = UserPreferences(location="Delhi", budget=Budget.LOW)
    _, user = PromptBuilder().build(
        prefs, [_candidate("Spice Route")], top_k=1, strict_json=True
    )
    assert "ONLY a single JSON object" in user


def test_prompt_length_reasonable():
    prefs = UserPreferences(location="Mumbai", budget=Budget.HIGH)
    candidates = [_candidate(f"Restaurant {i}") for i in range(25)]
    _, user = PromptBuilder().build(prefs, candidates, top_k=5)
    assert len(user) < 50_000
    assert json.loads(json.dumps(prefs.to_dict()))
