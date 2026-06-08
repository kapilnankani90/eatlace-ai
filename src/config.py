"""Application configuration from environment variables or Streamlit secrets."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get_config(name: str, default: str | None = None) -> str | None:
    # 1. Try environment variable
    val = os.getenv(name)
    if val is not None and val.strip():
        return val

    # 2. Try Streamlit secrets if available
    try:
        import streamlit as st
        if hasattr(st, "secrets") and name in st.secrets:
            val_secret = st.secrets[name]
            if val_secret is not None and str(val_secret).strip():
                return str(val_secret)
    except Exception:
        pass

    return default


DATASET_ID: str = _get_config(
    "DATASET_ID", "ManikaSaini/zomato-restaurant-recommendation"
)
HF_TOKEN: str | None = _get_config("HF_TOKEN") or None

INGESTION_MAX_RETRIES: int = int(_get_config("INGESTION_MAX_RETRIES", "3"))
INGESTION_RETRY_DELAY_SECONDS: float = float(
    _get_config("INGESTION_RETRY_DELAY_SECONDS", "2.0")
)


def _positive_int(name: str, default: int) -> int:
    raw = _get_config(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


MAX_CANDIDATES: int = _positive_int("MAX_CANDIDATES", 25)
TOP_K: int = min(_positive_int("TOP_K", 5), MAX_CANDIDATES)

# Groq (primary LLM provider)
GROQ_API_KEY: str | None = (
    _get_config("GROQ_API_KEY") or _get_config("LLM_API_KEY") or None
)
LLM_MODEL: str = _get_config("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE: float = float(_get_config("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS: int = _positive_int("LLM_MAX_TOKENS", 2000)
LLM_TIMEOUT_SECONDS: float = float(_get_config("LLM_TIMEOUT_SECONDS", "60"))
LLM_MAX_RETRIES: int = _positive_int("LLM_MAX_RETRIES", 1)
LLM_RETRY_DELAY_SECONDS: float = float(_get_config("LLM_RETRY_DELAY_SECONDS", "2.0"))

