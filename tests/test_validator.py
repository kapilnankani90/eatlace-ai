"""Tests for PreferenceValidator edge cases."""

import pytest

from src.models.preferences import Budget
from src.services.validator import PreferenceValidator, PreferenceValidationError


def test_optional_fields_default_none():
    prefs = PreferenceValidator().validate(location="Delhi", budget="low")
    assert prefs.cuisine is None
    assert prefs.min_rating is None
    assert prefs.additional_preferences is None


def test_whitespace_normalized():
    prefs = PreferenceValidator().validate(
        location="  Delhi  ",
        budget=" medium ",
    )
    assert prefs.location == "Delhi"
    assert prefs.budget == Budget.MEDIUM


def test_additional_preferences_truncated():
    long_text = "x" * 600
    prefs = PreferenceValidator().validate(
        location="Delhi",
        budget="low",
        additional_preferences=long_text,
    )
    assert prefs.additional_preferences is not None
    assert len(prefs.additional_preferences) == 500
