"""Tests for data ingestion with mocked Hugging Face load."""

from unittest.mock import patch

import pytest

from src.data.cache import DataCache
from src.data.ingestion import DataIngestionError, DataIngestionService


SAMPLE_ROWS = [
    {
        "name": "Mock Bistro",
        "location": "Connaught Place",
        "cuisines": "Italian",
        "rate": "4.0/5",
        "approx_cost(for two people)": "600",
        "votes": 50,
        "listed_in(city)": "Delhi",
    },
    {
        "name": "Second Spot",
        "location": "Koramangala",
        "cuisines": "Chinese",
        "rate": "3.8/5",
        "approx_cost(for two people)": "400",
        "votes": 20,
        "listed_in(city)": "Bangalore",
    },
]


class _MockSplit:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)


class _MockDataset:
    def __init__(self, rows: list[dict]) -> None:
        self._split = _MockSplit(rows)

    def __contains__(self, key: str) -> bool:
        return key == "train"

    def __getitem__(self, key: str) -> _MockSplit:
        return self._split

    def keys(self) -> list[str]:
        return ["train"]


def _mock_dataset(rows: list[dict]) -> _MockDataset:
    return _MockDataset(rows)


@patch("datasets.load_dataset")
def test_load_populates_cache(mock_load_dataset):
    mock_load_dataset.return_value = _mock_dataset(SAMPLE_ROWS)
    cache = DataCache()
    service = DataIngestionService(cache=cache)

    records = service.load()

    assert len(records) == 2
    assert cache.is_loaded()
    assert records[0].name in ("Mock Bistro", "Second Spot")
    meta = cache.get_metadata()
    assert meta.record_count == 2


@patch("datasets.load_dataset")
def test_load_uses_cache_when_already_loaded(mock_load_dataset):
    mock_load_dataset.return_value = _mock_dataset(SAMPLE_ROWS)
    cache = DataCache()
    service = DataIngestionService(cache=cache)

    service.load()
    service.load()

    mock_load_dataset.assert_called_once()


@patch("datasets.load_dataset")
def test_load_raises_on_empty_after_normalize(mock_load_dataset):
    mock_load_dataset.return_value = _mock_dataset(
        [{"name": "", "location": "X"}]
    )
    service = DataIngestionService(cache=DataCache())

    with pytest.raises(DataIngestionError):
        service.load()
