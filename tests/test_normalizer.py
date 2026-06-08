"""Unit tests for dataset normalization."""

import pytest

from src.data.normalizer import (
    compute_cost_percentiles,
    make_record_id,
    normalize_row,
    normalize_rows,
    parse_cost,
    parse_cuisines,
    parse_rating,
    reset_skip_stats,
)
from src.models.restaurant import RestaurantRecord


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("4.5/5", 4.5),
        ("4.1/5", 4.1),
        ("NEW", None),
        ("-", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_rating(raw, expected):
    assert parse_rating(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("300", 300.0),
        ("1,200", 1200.0),
        ("300-400", 350.0),
        ("₹800 for two", 800.0),
        ("", None),
        ("-", None),
    ],
)
def test_parse_cost(raw, expected):
    assert parse_cost(raw) == expected


def test_parse_cuisines_splits_and_trims():
    assert parse_cuisines("North Indian, Chinese, Fast Food") == [
        "North Indian",
        "Chinese",
        "Fast Food",
    ]
    assert parse_cuisines("") == []


def test_normalize_row_full_record():
    row = {
        "name": "Test Cafe",
        "location": "Banashankari",
        "cuisines": "Italian, Cafe",
        "rate": "4.2/5",
        "approx_cost(for two people)": "800",
        "votes": 100,
        "listed_in(city)": "Bangalore",
    }
    record = normalize_row(row)
    assert record is not None
    assert record.name == "Test Cafe"
    assert record.location == "Banashankari"
    assert record.cuisines == ["Italian", "Cafe"]
    assert record.rating == 4.2
    assert record.estimated_cost == 800.0
    assert record.metadata["votes"] == 100


def test_normalize_row_skips_missing_name():
    reset_skip_stats()
    assert normalize_row({"name": "", "location": "Delhi"}) is None


def test_normalize_row_uses_city_when_location_missing():
    row = {
        "name": "City Only Place",
        "location": "",
        "listed_in(city)": "Delhi",
        "cuisines": "Chinese",
        "rate": "3.5/5",
        "approx_cost(for two people)": "500",
    }
    record = normalize_row(row)
    assert record is not None
    assert record.location == "Delhi"


def test_normalize_row_rating_defaults_to_zero():
    row = {
        "name": "No Rating Spot",
        "location": "Koramangala",
        "cuisines": "Cafe",
        "rate": "NEW",
        "approx_cost(for two people)": "200",
    }
    record = normalize_row(row)
    assert record is not None
    assert record.rating == 0.0


def test_normalize_rows_deduplicates_by_id():
    rows = [
        {
            "name": "Dup Test",
            "location": "Indiranagar",
            "cuisines": "Cafe",
            "rate": "3.0/5",
            "approx_cost(for two people)": "300",
        },
        {
            "name": "Dup Test",
            "location": "Indiranagar",
            "cuisines": "Cafe",
            "rate": "4.5/5",
            "approx_cost(for two people)": "300",
        },
    ]
    records = normalize_rows(rows)
    assert len(records) == 1
    assert records[0].rating == 4.5


def test_make_record_id_stable():
    assert make_record_id("A", "B") == make_record_id("A", "B")
    assert make_record_id("A", "B") != make_record_id("A", "C")


def test_compute_cost_percentiles():
    records = [
        RestaurantRecord("1", "A", "X", [], 4.0, 100.0),
        RestaurantRecord("2", "B", "X", [], 4.0, 200.0),
        RestaurantRecord("3", "C", "X", [], 4.0, 300.0),
        RestaurantRecord("4", "D", "X", [], 4.0, 400.0),
        RestaurantRecord("5", "E", "X", [], 4.0, 500.0),
        RestaurantRecord("6", "F", "X", [], 4.0, 600.0),
        RestaurantRecord("7", "G", "X", [], 4.0, 700.0),
        RestaurantRecord("8", "H", "X", [], 4.0, 800.0),
        RestaurantRecord("9", "I", "X", [], 4.0, 900.0),
        RestaurantRecord("10", "J", "X", [], 4.0, 1000.0),
    ]
    p33, p66 = compute_cost_percentiles(records)
    assert p33 is not None
    assert p66 is not None
    assert p33 < p66


def test_compute_cost_percentiles_insufficient_data():
    records = [
        RestaurantRecord("1", "A", "X", [], 4.0, 100.0),
    ]
    assert compute_cost_percentiles(records) == (None, None)
