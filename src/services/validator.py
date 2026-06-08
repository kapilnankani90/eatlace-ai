"""Validate and normalize user preference input."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.models.preferences import Budget, UserPreferences

MAX_LOCATION_LENGTH = 200
MAX_CUISINE_LENGTH = 100
MAX_ADDITIONAL_LENGTH = 500
MIN_RATING_FLOOR = 0.0
MAX_RATING_CEILING = 5.0

BUDGET_SYNONYMS: dict[str, Budget] = {
    "low": Budget.LOW,
    "cheap": Budget.LOW,
    "budget": Budget.LOW,
    "medium": Budget.MEDIUM,
    "mid": Budget.MEDIUM,
    "moderate": Budget.MEDIUM,
    "high": Budget.HIGH,
    "expensive": Budget.HIGH,
    "pricey": Budget.HIGH,
    "premium": Budget.HIGH,
}


@dataclass
class ValidationErrorDetail:
    field: str
    message: str


class PreferenceValidationError(Exception):
    """Raised when user preferences fail validation."""

    def __init__(self, errors: list[ValidationErrorDetail]) -> None:
        self.errors = errors
        messages = "; ".join(f"{e.field}: {e.message}" for e in errors)
        super().__init__(messages)


class PreferenceValidator:
    """Parse raw inputs into UserPreferences or raise PreferenceValidationError."""

    def validate(
        self,
        *,
        location: str | None,
        budget: str | None,
        cuisine: str | None = None,
        min_rating: str | float | None = None,
        additional_preferences: str | None = None,
    ) -> UserPreferences:
        errors: list[ValidationErrorDetail] = []

        normalized_location = self._normalize_location(location, errors)
        normalized_budget = self._normalize_budget(budget, errors)
        normalized_cuisine = self._normalize_optional_text(
            cuisine, MAX_CUISINE_LENGTH, "cuisine", errors
        )
        normalized_rating = self._normalize_min_rating(min_rating, errors)
        normalized_additional = self._normalize_optional_text(
            additional_preferences,
            MAX_ADDITIONAL_LENGTH,
            "additional_preferences",
            errors,
        )

        if errors:
            raise PreferenceValidationError(errors)

        assert normalized_location is not None
        assert normalized_budget is not None

        return UserPreferences(
            location=normalized_location,
            budget=normalized_budget,
            cuisine=normalized_cuisine,
            min_rating=normalized_rating,
            additional_preferences=normalized_additional,
        )

    def _normalize_location(
        self, location: str | None, errors: list[ValidationErrorDetail]
    ) -> str | None:
        if location is None or not str(location).strip():
            errors.append(
                ValidationErrorDetail("location", "Location is required.")
            )
            return None
        text = re.sub(r"\s+", " ", str(location).strip())
        if len(text) > MAX_LOCATION_LENGTH:
            errors.append(
                ValidationErrorDetail(
                    "location",
                    f"Location must be at most {MAX_LOCATION_LENGTH} characters.",
                )
            )
            return None
        return text

    def _normalize_budget(
        self, budget: str | None, errors: list[ValidationErrorDetail]
    ) -> Budget | None:
        if budget is None or not str(budget).strip():
            errors.append(
                ValidationErrorDetail(
                    "budget",
                    "Budget is required (low, medium, or high).",
                )
            )
            return None
        key = str(budget).strip().lower()
        if key not in BUDGET_SYNONYMS:
            errors.append(
                ValidationErrorDetail(
                    "budget",
                    "Budget must be low, medium, or high.",
                )
            )
            return None
        return BUDGET_SYNONYMS[key]

    def _normalize_min_rating(
        self, min_rating: str | float | None, errors: list[ValidationErrorDetail]
    ) -> float | None:
        if min_rating is None or str(min_rating).strip() == "":
            return None
        try:
            value = float(min_rating)
        except (TypeError, ValueError):
            errors.append(
                ValidationErrorDetail(
                    "min_rating", "Minimum rating must be a number."
                )
            )
            return None
        if value < MIN_RATING_FLOOR or value > MAX_RATING_CEILING:
            errors.append(
                ValidationErrorDetail(
                    "min_rating",
                    f"Minimum rating must be between {MIN_RATING_FLOOR} and "
                    f"{MAX_RATING_CEILING}.",
                )
            )
            return None
        return value

    def _normalize_optional_text(
        self,
        value: str | None,
        max_length: int,
        field: str,
        errors: list[ValidationErrorDetail],
    ) -> str | None:
        if value is None or not str(value).strip():
            return None
        text = re.sub(r"\s+", " ", str(value).strip())
        if len(text) > max_length:
            text = text[:max_length]
        return text
