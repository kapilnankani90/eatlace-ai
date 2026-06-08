"""Application configuration dynamically resolved at runtime from environment variables or Streamlit secrets."""

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


# Default static values
_DEFAULTS = {
    "DATASET_ID": "ManikaSaini/zomato-restaurant-recommendation",
    "HF_TOKEN": None,
    "INGESTION_MAX_RETRIES": "3",
    "INGESTION_RETRY_DELAY_SECONDS": "2.0",
    "MAX_CANDIDATES": "25",
    "TOP_K": "5",
    "GROQ_API_KEY": None,
    "LLM_MODEL": "llama-3.3-70b-versatile",
    "LLM_TEMPERATURE": "0.3",
    "LLM_MAX_TOKENS": "2000",
    "LLM_TIMEOUT_SECONDS": "60",
    "LLM_MAX_RETRIES": "1",
    "LLM_RETRY_DELAY_SECONDS": "2.0",
}


def __getattr__(name: str):
    """Dynamically get configuration at runtime (ensures Streamlit secrets are loaded)."""
    if name not in _DEFAULTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    default = _DEFAULTS[name]
    val = _get_config(name, default)

    # Convert to appropriate types
    if name in ["INGESTION_MAX_RETRIES", "MAX_CANDIDATES", "LLM_MAX_TOKENS", "LLM_MAX_RETRIES"]:
        try:
            return int(val) if val is not None else int(default)
        except ValueError:
            return int(default)
    elif name == "TOP_K":
        try:
            top_k_val = int(val) if val is not None else int(default)
            max_cand = __getattr__("MAX_CANDIDATES")
            return min(top_k_val, max_cand)
        except ValueError:
            return int(default)
    elif name in ["INGESTION_RETRY_DELAY_SECONDS", "LLM_TEMPERATURE", "LLM_TIMEOUT_SECONDS", "LLM_RETRY_DELAY_SECONDS"]:
        try:
            return float(val) if val is not None else float(default)
        except ValueError:
            return float(default)

    # String or None types
    return val
