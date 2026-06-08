"""Load Zomato dataset from Hugging Face and populate the cache."""

from __future__ import annotations

import logging
import time
from typing import Any

from src import config
from src.data.cache import DataCache, get_cache
from src.data.normalizer import (
    compute_cost_percentiles,
    get_skip_stats,
    normalize_rows,
)
from src.models.restaurant import RestaurantRecord

logger = logging.getLogger(__name__)


class DataIngestionError(Exception):
    """Raised when dataset cannot be loaded or is empty after normalization."""


class DataIngestionService:
    """Loads, normalizes, and caches restaurant records."""

    def __init__(
        self,
        dataset_id: str | None = None,
        cache: DataCache | None = None,
        hf_token: str | None = None,
    ) -> None:
        self.dataset_id = dataset_id or config.DATASET_ID
        self.cache = cache or get_cache()
        self.hf_token = hf_token if hf_token is not None else config.HF_TOKEN

    def load(self, *, force: bool = False) -> list[RestaurantRecord]:
        if self.cache.is_loaded() and not force:
            return self.cache.get_records()

        raw_rows = self._download_with_retry()
        records = normalize_rows(raw_rows)

        if not records:
            raise DataIngestionError(
                f"No valid restaurant records after normalization for '{self.dataset_id}'. "
                "Check dataset schema or normalizer column mappings."
            )

        p33, p66 = compute_cost_percentiles(records)
        self.cache.set_records(
            records,
            cost_percentile_33=p33,
            cost_percentile_66=p66,
            skipped=get_skip_stats(),
        )

        meta = self.cache.get_metadata()
        logger.info(
            "Loaded %s records (skipped: %s, cost p33=%s, p66=%s)",
            meta.record_count,
            meta.skipped,
            meta.cost_percentile_33,
            meta.cost_percentile_66,
        )
        return records

    def _download_with_retry(self) -> list[dict[str, Any]]:
        last_error: Exception | None = None
        for attempt in range(1, config.INGESTION_MAX_RETRIES + 1):
            try:
                return self._fetch_dataset()
            except Exception as exc:  # noqa: BLE001 - retry on any load failure
                last_error = exc
                logger.warning(
                    "Dataset load attempt %s/%s failed: %s",
                    attempt,
                    config.INGESTION_MAX_RETRIES,
                    exc,
                )
                if attempt < config.INGESTION_MAX_RETRIES:
                    delay = config.INGESTION_RETRY_DELAY_SECONDS * attempt
                    time.sleep(delay)

        raise DataIngestionError(
            f"Failed to load dataset '{self.dataset_id}' after "
            f"{config.INGESTION_MAX_RETRIES} attempts: {last_error}"
        ) from last_error

    def _fetch_dataset(self) -> list[dict[str, Any]]:
        try:
            from datasets import load_dataset
        except ImportError as exc:
            raise DataIngestionError(
                "Install dependencies: pip install -r requirements.txt"
            ) from exc

        kwargs: dict[str, Any] = {}
        if self.hf_token:
            kwargs["token"] = self.hf_token

        dataset = load_dataset(self.dataset_id, **kwargs)
        split_name = "train" if "train" in dataset else list(dataset.keys())[0]
        split = dataset[split_name]

        rows: list[dict[str, Any]] = []
        for item in split:
            rows.append(dict(item))
        return rows
