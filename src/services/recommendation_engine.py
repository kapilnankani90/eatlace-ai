"""LLM-powered ranking and explanation for filtered candidates."""

from __future__ import annotations

import logging

from src import config
from src.models.preferences import UserPreferences
from src.models.recommendation import RecommendationResult
from src.models.restaurant import RestaurantRecord
from src.services.llm_client import GroqLLMClient, LLMClient, LLMError
from src.services.parser import LLMResponseParser
from src.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    candidates + preferences → prompt → LLM → parsed RecommendationResult.
    Falls back to rating-based ranking when LLM or parsing fails.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        parser: LLMResponseParser | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.parser = parser or LLMResponseParser()

    def recommend(
        self,
        prefs: UserPreferences,
        candidates: list[RestaurantRecord],
        *,
        top_k: int | None = None,
        filter_messages: list[str] | None = None,
    ) -> RecommendationResult:
        messages = list(filter_messages or [])
        k = min(top_k or config.TOP_K, len(candidates))

        if not candidates:
            return RecommendationResult(
                recommendations=[],
                filter_messages=messages,
            )

        if k < 1:
            k = len(candidates)

        try:
            parsed, used_fallback = self._recommend_with_llm(prefs, candidates, k)
            return RecommendationResult(
                recommendations=parsed.recommendations,
                summary=parsed.summary,
                used_fallback=used_fallback,
                filter_messages=messages,
            )
        except (LLMError, ValueError) as exc:
            logger.warning("LLM recommendation failed, using fallback: %s", exc)
            fallback = self.parser.build_fallback(candidates, k)
            return RecommendationResult(
                recommendations=fallback.recommendations,
                summary=fallback.summary,
                used_fallback=True,
                filter_messages=messages,
            )

    def _recommend_with_llm(
        self,
        prefs: UserPreferences,
        candidates: list[RestaurantRecord],
        top_k: int,
    ) -> tuple:
        client = self.llm_client or GroqLLMClient()

        system, user = self.prompt_builder.build(prefs, candidates, top_k=top_k)
        raw = client.complete(system, user)

        try:
            parsed = self.parser.parse(raw, candidates, top_k=top_k)
            return parsed, False
        except ValueError as first_error:
            logger.warning("Parse failed, retrying with strict JSON prompt: %s", first_error)
            system, user = self.prompt_builder.build(
                prefs, candidates, top_k=top_k, strict_json=True
            )
            raw = client.complete(system, user)
            parsed = self.parser.parse(raw, candidates, top_k=top_k)
            return parsed, False
