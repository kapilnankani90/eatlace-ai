"""LLM client abstraction and Groq provider implementation."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from src import config

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM provider fails after retries."""


class LLMClient(ABC):
    """Provider-agnostic LLM interface."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return raw text completion from the model."""


class GroqLLMClient(LLMClient):
    """Groq Chat Completions API (default production provider)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.api_key = api_key or config.GROQ_API_KEY
        self.model = model or config.LLM_MODEL
        self.temperature = (
            temperature if temperature is not None else config.LLM_TEMPERATURE
        )
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        self.timeout = timeout or config.LLM_TIMEOUT_SECONDS
        self.max_retries = (
            max_retries if max_retries is not None else config.LLM_MAX_RETRIES
        )

        if not self.api_key:
            raise LLMError(
                "GROQ_API_KEY is not set. Add it to your .env file "
                "(see .env.example). Get a key at https://console.groq.com/keys"
            )

    def complete(self, system: str, user: str) -> str:
        try:
            from groq import Groq
        except ImportError as exc:
            raise LLMError(
                "Install the Groq SDK: pip install groq"
            ) from exc

        client = Groq(api_key=self.api_key, timeout=self.timeout)
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 2):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise LLMError("Groq returned an empty response.")
                return content.strip()
            except Exception as exc:  # noqa: BLE001 - map Groq SDK errors
                last_error = exc
                if _is_retryable_groq_error(exc) and attempt <= self.max_retries:
                    delay = config.LLM_RETRY_DELAY_SECONDS * attempt
                    logger.warning(
                        "Groq transient error, retrying in %ss: %s", delay, exc
                    )
                    time.sleep(delay)
                    continue
                if _is_auth_error(exc):
                    raise LLMError(
                        "Invalid Groq API key. Check GROQ_API_KEY in your .env file."
                    ) from exc
                raise LLMError(f"Groq request failed: {exc}") from exc

        raise LLMError(f"Groq request failed after retries: {last_error}")


def _is_auth_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status == 401:
        return True
    message = str(exc).lower()
    return "401" in message or "invalid api key" in message


def _is_retryable_groq_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status in (429, 500, 502, 503, 504):
        return True
    name = type(exc).__name__
    if name in ("APIConnectionError", "APITimeoutError", "RateLimitError"):
        return True
    return False


class MockLLMClient(LLMClient):
    """Deterministic client for tests."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.response
