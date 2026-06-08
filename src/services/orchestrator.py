"""End-to-end recommendation orchestration."""

from __future__ import annotations

import logging
import time

from src import config
from src.data.cache import DataCache, get_cache
from src.data.ingestion import DataIngestionError, DataIngestionService
from src.models.preferences import UserPreferences
from src.models.recommendation import RecommendationResult
from src.services.filter import RestaurantFilterService
from src.services.llm_client import LLMClient, LLMError
from src.services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class OrchestratorError(Exception):
    """Raised when the pipeline cannot proceed (e.g. dataset load failure)."""


class RecommendationOrchestrator:
    """
    Single entry point: load data → filter → Groq recommend → result.

    Never calls the LLM when the filtered candidate list is empty.
    """

    def __init__(
        self,
        ingestion_service: DataIngestionService | None = None,
        filter_service: RestaurantFilterService | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        cache: DataCache | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.cache = cache or get_cache()
        self.ingestion_service = ingestion_service or DataIngestionService(
            cache=self.cache
        )
        self.filter_service = filter_service or RestaurantFilterService()
        self.recommendation_engine = recommendation_engine or RecommendationEngine(
            llm_client=llm_client
        )

    def recommend(
        self,
        prefs: UserPreferences,
        *,
        force_reload: bool = False,
        top_k: int | None = None,
        require_groq_key: bool = True,
    ) -> RecommendationResult:
        self.ensure_data_loaded(force=force_reload)

        meta = self.cache.get_metadata()
        t0 = time.perf_counter()

        filter_result = self.filter_service.filter(
            prefs,
            self.cache.get_records(),
            cost_percentile_33=meta.cost_percentile_33,
            cost_percentile_66=meta.cost_percentile_66,
        )

        logger.info(
            "Filtered to %d candidates (%.2fs)",
            len(filter_result.candidates),
            time.perf_counter() - t0,
        )

        if not filter_result.candidates:
            return RecommendationResult(
                recommendations=[],
                filter_messages=filter_result.messages,
            )

        if (
            require_groq_key
            and not config.GROQ_API_KEY
            and self.recommendation_engine.llm_client is None
        ):
            raise LLMError(
                "GROQ_API_KEY is not set. Add it to your .env file "
                "(see .env.example)."
            )

        t1 = time.perf_counter()

        try:
            result = self.recommendation_engine.recommend(
                prefs,
                filter_result.candidates,
                top_k=top_k,
                filter_messages=filter_result.messages,
            )
        except LLMError:
            raise
        except Exception as exc:
            raise OrchestratorError(f"Recommendation failed: {exc}") from exc

        logger.info(
            "Recommendations ready: count=%d fallback=%s (%.2fs)",
            len(result.recommendations),
            result.used_fallback,
            time.perf_counter() - t1,
        )
        return result

    def ensure_data_loaded(self, *, force: bool = False) -> None:
        if self.cache.is_loaded() and not force:
            return
        try:
            self.ingestion_service.load(force=force)
        except DataIngestionError as exc:
            raise OrchestratorError(str(exc)) from exc
        if not self.cache.is_loaded():
            raise OrchestratorError("Dataset failed to load into cache.")
