"""Unit tests for preference validation and restaurant filtering."""

import pytest

from src.models.preferences import Budget, UserPreferences
from src.models.restaurant import RestaurantRecord
from src.services.filter import RestaurantFilterService
from src.services.validator import PreferenceValidationError, PreferenceValidator


def _record(
    name: str,
    location: str,
    cuisines: list[str],
    rating: float,
    cost: float | None,
    city: str | None = None,
    votes: int = 0,
) -> RestaurantRecord:
    metadata: dict = {"votes": votes}
    if city:
        metadata["listed_in(city)"] = city
    return RestaurantRecord(
        id=name,
        name=name,
        location=location,
        cuisines=cuisines,
        rating=rating,
        estimated_cost=cost,
        metadata=metadata,
    )


SAMPLE_RECORDS = [
    _record("A", "Indiranagar", ["Italian"], 4.5, 200.0, city="Bangalore", votes=100),
    _record("B", "Indiranagar", ["Chinese"], 4.0, 500.0, city="Bangalore", votes=80),
    _record("C", "Connaught Place", ["Italian"], 3.5, 800.0, city="Delhi", votes=50),
    _record("D", "Koramangala", ["Cafe"], 4.8, 150.0, city="Bangalore", votes=200),
    _record("E", "Banashankari", ["South Indian"], 4.2, 350.0, city="Bangalore", votes=60),
]

P33 = 300.0
P66 = 600.0


class TestPreferenceValidator:
    def test_valid_preferences(self):
        prefs = PreferenceValidator().validate(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating="4.0",
            additional_preferences="family-friendly",
        )
        assert prefs.location == "Bangalore"
        assert prefs.budget == Budget.MEDIUM
        assert prefs.cuisine == "Italian"
        assert prefs.min_rating == 4.0

    def test_budget_synonyms(self):
        v = PreferenceValidator()
        assert v.validate(location="Delhi", budget="cheap").budget == Budget.LOW
        assert v.validate(location="Delhi", budget="pricey").budget == Budget.HIGH

    def test_missing_location(self):
        with pytest.raises(PreferenceValidationError) as exc:
            PreferenceValidator().validate(location="", budget="low")
        assert any(e.field == "location" for e in exc.value.errors)

    def test_invalid_budget(self):
        with pytest.raises(PreferenceValidationError):
            PreferenceValidator().validate(location="Delhi", budget="luxury")

    def test_invalid_min_rating(self):
        with pytest.raises(PreferenceValidationError):
            PreferenceValidator().validate(location="Delhi", budget="low", min_rating="9")


class TestRestaurantFilterService:
    def test_location_substring(self):
        prefs = UserPreferences("Indiranagar", Budget.MEDIUM)
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=P33, cost_percentile_66=P66
        )
        names = {r.name for r in result.candidates}
        assert names == {"A", "B"}

    def test_location_by_city_metadata(self):
        prefs = UserPreferences("Bangalore", Budget.MEDIUM)
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=P33, cost_percentile_66=P66
        )
        assert len(result.candidates) == 4
        assert "C" not in {r.name for r in result.candidates}

    def test_cuisine_filter(self):
        prefs = UserPreferences("Bangalore", Budget.MEDIUM, cuisine="Italian")
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=P33, cost_percentile_66=P66
        )
        assert {r.name for r in result.candidates} == {"A"}

    def test_min_rating_filter(self):
        prefs = UserPreferences("Bangalore", Budget.LOW, min_rating=4.3)
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=P33, cost_percentile_66=P66
        )
        assert {r.name for r in result.candidates} == {"A", "D"}

    def test_budget_low(self):
        prefs = UserPreferences("Bangalore", Budget.LOW)
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=P33, cost_percentile_66=P66
        )
        names = {r.name for r in result.candidates}
        assert "D" in names
        assert "B" not in names

    def test_budget_high(self):
        prefs = UserPreferences("Delhi", Budget.HIGH)
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=P33, cost_percentile_66=P66
        )
        assert {r.name for r in result.candidates} == {"C"}

    def test_cap_respected(self):
        many = [
            _record(f"R{i}", "Zone", ["Cafe"], 4.0 + i * 0.01, 400.0, city="Metro")
            for i in range(30)
        ]
        prefs = UserPreferences("Metro", Budget.MEDIUM)
        result = RestaurantFilterService(max_candidates=5).filter(
            prefs, many, cost_percentile_33=P33, cost_percentile_66=P66
        )
        assert len(result.candidates) == 5

    def test_sort_by_rating_then_votes(self):
        records = [
            _record("Low", "X", ["Cafe"], 4.0, 400.0, votes=10),
            _record("High", "X", ["Cafe"], 4.5, 400.0, votes=5),
            _record("Votes", "X", ["Cafe"], 4.5, 400.0, votes=100),
        ]
        prefs = UserPreferences("X", Budget.MEDIUM)
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, records, cost_percentile_33=P33, cost_percentile_66=P66
        )
        assert [r.name for r in result.candidates] == ["Votes", "High", "Low"]

    def test_relax_cuisine_when_no_match(self):
        records = [
            _record("Only Chinese", "Y", ["Chinese"], 4.0, 400.0),
        ]
        prefs = UserPreferences("Y", Budget.MEDIUM, cuisine="Italian")
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, records, cost_percentile_33=P33, cost_percentile_66=P66
        )
        assert len(result.candidates) == 1
        assert any("cuisine" in m.lower() for m in result.messages)

    def test_empty_after_all_relaxations(self):
        prefs = UserPreferences("Nonexistent City", Budget.LOW)
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=P33, cost_percentile_66=P66
        )
        assert result.is_empty
        assert any("No restaurants found" in m for m in result.messages)

    def test_skips_budget_when_no_percentiles(self):
        prefs = UserPreferences("Bangalore", Budget.LOW)
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=None, cost_percentile_66=None
        )
        assert len(result.candidates) == 4

    def test_multiple_cuisines_any_match(self):
        prefs = UserPreferences("Bangalore", Budget.MEDIUM, cuisine="Italian and Chinese")
        result = RestaurantFilterService(max_candidates=10).filter(
            prefs, SAMPLE_RECORDS, cost_percentile_33=P33, cost_percentile_66=P66
        )
        names = {r.name for r in result.candidates}
        assert "A" in names
        assert "B" in names
