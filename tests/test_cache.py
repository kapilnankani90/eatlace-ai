"""Unit tests for in-memory data cache."""

from src.data.cache import DataCache
from src.models.restaurant import RestaurantRecord


def test_cache_load_and_metadata():
    cache = DataCache()
    assert not cache.is_loaded()

    records = [
        RestaurantRecord("1", "A", "Delhi", ["Indian"], 4.0, 500.0),
    ]
    cache.set_records(records, cost_percentile_33=300.0, cost_percentile_66=800.0)

    assert cache.is_loaded()
    assert len(cache.get_records()) == 1
    meta = cache.get_metadata()
    assert meta.record_count == 1
    assert meta.cost_percentile_33 == 300.0
    assert meta.cost_percentile_66 == 800.0


def test_cache_clear():
    cache = DataCache()
    cache.set_records([], cost_percentile_33=None, cost_percentile_66=None)
    cache.clear()
    assert not cache.is_loaded()
    assert cache.get_records() == []
