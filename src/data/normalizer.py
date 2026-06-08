"""Map raw Hugging Face rows to RestaurantRecord instances."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from src.models.restaurant import RestaurantRecord

# Canonical column names from ManikaSaini/zomato-restaurant-recommendation
COL_NAME = "name"
COL_LOCATION = "location"
COL_CUISINES = "cuisines"
COL_RATE = "rate"
COL_COST = "approx_cost(for two people)"
COL_CITY = "listed_in(city)"
COL_VOTES = "votes"
COL_ADDRESS = "address"
COL_REST_TYPE = "rest_type"

COST_COLUMN_ALIASES = (
    COL_COST,
    "approx_cost",
    "average_cost_for_two",
    "cost",
)

SKIP_STATS: dict[str, int] = {
    "missing_name": 0,
    "missing_location": 0,
    "duplicate": 0,
}


def reset_skip_stats() -> None:
    for key in SKIP_STATS:
        SKIP_STATS[key] = 0


def get_skip_stats() -> dict[str, int]:
    return dict(SKIP_STATS)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN
        return True
    text = str(value).strip().lower()
    return text in ("", "nan", "none", "null", "-")


def _clean_str(value: Any) -> str:
    return str(value).strip()


def parse_rating(raw: Any) -> float | None:
    """Parse Zomato rate field (e.g. '4.1/5', 'NEW', '-')."""
    if _is_empty(raw):
        return None
    text = _clean_str(raw)
    if text.upper() == "NEW":
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    rating = float(match.group(1))
    if rating > 5.0:
        rating = rating / 10.0 if rating <= 10.0 else 5.0
    return max(0.0, min(5.0, rating))


def parse_cost(raw: Any) -> float | None:
    """Parse cost strings: '300', '1,200', '300-400', '₹800'."""
    if _is_empty(raw):
        return None
    text = _clean_str(raw)
    numbers = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
    if not numbers:
        return None
    values = [float(n) for n in numbers]
    if len(values) == 1:
        cost = values[0]
    else:
        cost = sum(values) / len(values)
    return cost if cost > 0 else None


def parse_cuisines(raw: Any) -> list[str]:
    if _is_empty(raw):
        return []
    text = _clean_str(raw)
    parts = re.split(r"[,;]", text)
    return [p.strip() for p in parts if p.strip()]


def make_record_id(name: str, location: str) -> str:
    key = f"{name.lower()}|{location.lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _resolve_cost_column(row: dict[str, Any]) -> Any:
    for col in COST_COLUMN_ALIASES:
        if col in row and not _is_empty(row[col]):
            return row[col]
    return None


def normalize_row(row: dict[str, Any]) -> RestaurantRecord | None:
    """Convert one raw dataset dict to RestaurantRecord, or None to skip."""
    name = _clean_str(row.get(COL_NAME, ""))
    if _is_empty(name):
        SKIP_STATS["missing_name"] += 1
        return None

    location = _clean_str(row.get(COL_LOCATION, ""))
    if _is_empty(location):
        city = row.get(COL_CITY)
        if not _is_empty(city):
            location = _clean_str(city)
    if _is_empty(location):
        SKIP_STATS["missing_location"] += 1
        return None

    rating = parse_rating(row.get(COL_RATE))
    if rating is None:
        rating = 0.0

    cuisines = parse_cuisines(row.get(COL_CUISINES))
    estimated_cost = parse_cost(_resolve_cost_column(row))

    metadata: dict[str, Any] = {}
    for key in (COL_VOTES, COL_ADDRESS, COL_REST_TYPE, COL_CITY, "url"):
        if key in row and not _is_empty(row[key]):
            metadata[key] = row[key]

    return RestaurantRecord(
        id=make_record_id(name, location),
        name=name,
        location=location,
        cuisines=cuisines,
        rating=rating,
        estimated_cost=estimated_cost,
        metadata=metadata,
    )


def normalize_rows(rows: list[dict[str, Any]]) -> list[RestaurantRecord]:
    """Normalize rows and deduplicate by record id (keep higher rating)."""
    reset_skip_stats()
    by_id: dict[str, RestaurantRecord] = {}

    for row in rows:
        record = normalize_row(row)
        if record is None:
            continue
        existing = by_id.get(record.id)
        if existing is None:
            by_id[record.id] = record
        else:
            SKIP_STATS["duplicate"] += 1
            if record.rating > existing.rating:
                by_id[record.id] = record

    return list(by_id.values())


def compute_cost_percentiles(
    records: list[RestaurantRecord],
) -> tuple[float | None, float | None]:
    """Return (33rd, 66th) percentile of estimated_cost for budget bands."""
    costs = sorted(
        r.estimated_cost for r in records if r.estimated_cost is not None
    )
    if len(costs) < 10:
        return None, None

    def percentile(p: float) -> float:
        idx = (len(costs) - 1) * p
        lower = int(idx)
        upper = min(lower + 1, len(costs) - 1)
        weight = idx - lower
        return costs[lower] * (1 - weight) + costs[upper] * weight

    return percentile(0.33), percentile(0.66)
