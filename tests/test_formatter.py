"""Tests for ResultFormatter."""

from src.models.recommendation import Recommendation, RecommendationResult
from src.models.restaurant import RestaurantRecord
from src.services.formatter import ResultFormatter


def test_format_cli_includes_explanation_and_rating():
    record = RestaurantRecord(
        id="1",
        name="Test Place",
        location="Area",
        cuisines=["Italian"],
        rating=4.5,
        estimated_cost=600.0,
    )
    result = RecommendationResult(
        recommendations=[
            Recommendation(rank=1, restaurant=record, explanation="Perfect fit.")
        ],
        summary="Enjoy!",
    )
    text = ResultFormatter().format_cli(result)
    assert "Test Place" in text
    assert "Perfect fit." in text
    assert "4.5" in text
    assert "Summary: Enjoy!" in text
