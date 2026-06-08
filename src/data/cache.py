"""In-memory cache for normalized restaurant data and budget percentiles."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from src.models.restaurant import RestaurantRecord


@dataclass
class CacheMetadata:
    record_count: int = 0
    cost_percentile_33: float | None = None
    cost_percentile_66: float | None = None
    skipped: dict[str, int] | None = None


class DataCache:
    """Thread-safe store for loaded restaurant records."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: list[RestaurantRecord] = []
        self._metadata = CacheMetadata()
        self._loaded = False

    def is_loaded(self) -> bool:
        with self._lock:
            return self._loaded

    def get_records(self) -> list[RestaurantRecord]:
        with self._lock:
            return list(self._records)

    def get_metadata(self) -> CacheMetadata:
        with self._lock:
            return CacheMetadata(
                record_count=self._metadata.record_count,
                cost_percentile_33=self._metadata.cost_percentile_33,
                cost_percentile_66=self._metadata.cost_percentile_66,
                skipped=dict(self._metadata.skipped or {}),
            )

    def set_records(
        self,
        records: list[RestaurantRecord],
        *,
        cost_percentile_33: float | None,
        cost_percentile_66: float | None,
        skipped: dict[str, int] | None = None,
    ) -> None:
        with self._lock:
            self._records = list(records)
            self._metadata = CacheMetadata(
                record_count=len(self._records),
                cost_percentile_33=cost_percentile_33,
                cost_percentile_66=cost_percentile_66,
                skipped=skipped,
            )
            self._loaded = True

    def clear(self) -> None:
        with self._lock:
            self._records = []
            self._metadata = CacheMetadata()
            self._loaded = False


_default_cache: DataCache | None = None
_cache_lock = threading.Lock()


def get_cache() -> DataCache:
    global _default_cache
    with _cache_lock:
        if _default_cache is None:
            _default_cache = DataCache()
        return _default_cache
