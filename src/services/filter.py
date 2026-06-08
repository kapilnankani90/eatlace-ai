"""Filter restaurant records by user preferences."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto

from src import config
from src.models.preferences import Budget, UserPreferences
from src.models.restaurant import RestaurantRecord

COL_CITY = "listed_in(city)"


class BudgetMatchMode(Enum):
    STRICT = auto()
    RELAXED = auto()


@dataclass
class FilterResult:
    """Outcome of filtering with optional relaxation notices."""

    candidates: list[RestaurantRecord] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.candidates) == 0


class RestaurantFilterService:
    """Apply preference filters and relax constraints when no matches found."""

    def __init__(self, max_candidates: int | None = None) -> None:
        self.max_candidates = max_candidates or config.MAX_CANDIDATES
        if self.max_candidates < 1:
            self.max_candidates = 25

    def filter(
        self,
        prefs: UserPreferences,
        records: list[RestaurantRecord],
        *,
        cost_percentile_33: float | None = None,
        cost_percentile_66: float | None = None,
    ) -> FilterResult:
        messages: list[str] = []

        candidates = self._apply_pipeline(
            prefs,
            records,
            cost_percentile_33=cost_percentile_33,
            cost_percentile_66=cost_percentile_66,
        )

        if candidates:
            return FilterResult(
                candidates=self._cap_and_sort(candidates),
                messages=messages,
            )

        # Relaxation step 1: drop cuisine
        if prefs.cuisine:
            relaxed = prefs.with_cuisine(None)
            candidates = self._apply_pipeline(
                relaxed,
                records,
                cost_percentile_33=cost_percentile_33,
                cost_percentile_66=cost_percentile_66,
            )
            if candidates:
                messages.append(
                    f"No exact cuisine match; showing all cuisines in {prefs.location}."
                )
                return FilterResult(
                    candidates=self._cap_and_sort(candidates),
                    messages=messages,
                )

        # Relaxation step 2: lower min_rating by 0.5
        if prefs.min_rating is not None and prefs.min_rating > 0:
            new_rating = max(0.0, prefs.min_rating - 0.5)
            relaxed = prefs.with_cuisine(None).with_min_rating(new_rating)
            candidates = self._apply_pipeline(
                relaxed,
                records,
                cost_percentile_33=cost_percentile_33,
                cost_percentile_66=cost_percentile_66,
            )
            if candidates:
                messages.append("Relaxed rating requirement.")
                return FilterResult(
                    candidates=self._cap_and_sort(candidates),
                    messages=messages,
                )

        # Relaxation step 3: widen budget one band
        relaxed = prefs.with_cuisine(None)
        if prefs.min_rating is not None and prefs.min_rating > 0:
            relaxed = relaxed.with_min_rating(max(0.0, prefs.min_rating - 0.5))

        candidates = self._apply_pipeline(
            relaxed,
            records,
            cost_percentile_33=cost_percentile_33,
            cost_percentile_66=cost_percentile_66,
            budget_mode=BudgetMatchMode.RELAXED,
        )
        if candidates:
            messages.append("Relaxed budget to show more options.")
            return FilterResult(
                candidates=self._cap_and_sort(candidates),
                messages=messages,
            )

        messages.append(
            f"No restaurants found for {prefs.location}. Try another city or broader filters."
        )
        return FilterResult(candidates=[], messages=messages)

    def _apply_pipeline(
        self,
        prefs: UserPreferences,
        records: list[RestaurantRecord],
        *,
        cost_percentile_33: float | None,
        cost_percentile_66: float | None,
        budget_mode: BudgetMatchMode = BudgetMatchMode.STRICT,
    ) -> list[RestaurantRecord]:
        result = records
        result = [r for r in result if self._matches_location(r, prefs.location)]
        if prefs.cuisine:
            cuisines = self._split_cuisine_query(prefs.cuisine)
            result = [
                r
                for r in result
                if self._matches_any_cuisine(r, cuisines)
            ]
        if prefs.min_rating is not None:
            result = [r for r in result if r.rating >= prefs.min_rating]
        result = [
            r
            for r in result
            if self._matches_budget(
                r,
                prefs.budget,
                cost_percentile_33,
                cost_percentile_66,
                mode=budget_mode,
            )
        ]
        return result

    def _cap_and_sort(self, records: list[RestaurantRecord]) -> list[RestaurantRecord]:
        sorted_records = sorted(
            records,
            key=lambda r: (
                -r.rating,
                -self._vote_count(r),
                r.name.lower(),
            ),
        )
        return sorted_records[: self.max_candidates]

    @staticmethod
    def _vote_count(record: RestaurantRecord) -> int:
        votes = record.metadata.get("votes")
        if isinstance(votes, int):
            return votes
        try:
            return int(votes) if votes is not None else 0
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _matches_location(record: RestaurantRecord, query: str) -> bool:
        q = query.strip().lower()
        if not q:
            return False
        if q in record.location.lower():
            return True
        city = record.metadata.get(COL_CITY)
        if city and q in str(city).lower():
            return True
        return False

    @staticmethod
    def _split_cuisine_query(cuisine: str) -> list[str]:
        parts = re.split(r"\s+and\s+|,|;", cuisine, flags=re.IGNORECASE)
        return [p.strip().lower() for p in parts if p.strip()]

    @staticmethod
    def _matches_any_cuisine(record: RestaurantRecord, queries: list[str]) -> bool:
        if not queries:
            return True
        haystack = " ".join(c.lower() for c in record.cuisines)
        return any(q in haystack for q in queries)

    @staticmethod
    def _matches_budget(
        record: RestaurantRecord,
        budget: Budget,
        p33: float | None,
        p66: float | None,
        *,
        mode: BudgetMatchMode = BudgetMatchMode.STRICT,
    ) -> bool:
        cost = record.estimated_cost
        if p33 is None or p66 is None:
            return True
        if cost is None:
            return False

        if mode == BudgetMatchMode.STRICT:
            if budget == Budget.LOW:
                return cost <= p33
            if budget == Budget.MEDIUM:
                return cost <= p66
            return cost > p66

        # Relaxed: widen by one band
        if budget == Budget.LOW:
            return cost <= p66
        if budget == Budget.HIGH:
            return cost > p33
        return True
