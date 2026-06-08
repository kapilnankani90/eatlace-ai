"""User preference domain model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Budget(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class UserPreferences:
    """Validated user inputs for restaurant filtering."""

    location: str
    budget: Budget
    cuisine: str | None = None
    min_rating: float | None = None
    additional_preferences: str | None = None

    def to_dict(self) -> dict:
        return {
            "location": self.location,
            "budget": self.budget.value,
            "cuisine": self.cuisine,
            "min_rating": self.min_rating,
            "additional_preferences": self.additional_preferences,
        }

    def with_cuisine(self, cuisine: str | None) -> UserPreferences:
        return UserPreferences(
            location=self.location,
            budget=self.budget,
            cuisine=cuisine,
            min_rating=self.min_rating,
            additional_preferences=self.additional_preferences,
        )

    def with_min_rating(self, min_rating: float | None) -> UserPreferences:
        return UserPreferences(
            location=self.location,
            budget=self.budget,
            cuisine=self.cuisine,
            min_rating=min_rating,
            additional_preferences=self.additional_preferences,
        )

    def with_budget(self, budget: Budget) -> UserPreferences:
        return UserPreferences(
            location=self.location,
            budget=budget,
            cuisine=self.cuisine,
            min_rating=self.min_rating,
            additional_preferences=self.additional_preferences,
        )
