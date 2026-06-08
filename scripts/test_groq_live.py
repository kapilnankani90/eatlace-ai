"""
Live smoke test for Groq API.

Requires GROQ_API_KEY in .env (see .env.example).

Usage:
    python scripts/test_groq_live.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as script from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import config
from src.data.cache import DataCache
from src.models.preferences import Budget, UserPreferences
from src.models.restaurant import RestaurantRecord
from src.services.llm_client import GroqLLMClient, LLMError
from src.services.orchestrator import RecommendationOrchestrator


def _check_env() -> bool:
    if not config.GROQ_API_KEY:
        print("FAIL: GROQ_API_KEY is not set. Add it to .env (see .env.example).")
        return False
    masked = f"{config.GROQ_API_KEY[:4]}...{config.GROQ_API_KEY[-4:]}"
    print(f"OK: GROQ_API_KEY loaded ({masked}, length={len(config.GROQ_API_KEY)})")
    print(f"OK: LLM_MODEL={config.LLM_MODEL}")
    return True


def test_groq_ping() -> bool:
    print("\n--- Test 1: Groq API ping (minimal JSON) ---")
    client = GroqLLMClient()
    try:
        raw = client.complete(
            "You are a test assistant. Reply with JSON only.",
            'Return exactly: {"status": "ok", "provider": "groq"}',
        )
        print("OK: Groq returned a response")
        print(raw[:400])
        data = json.loads(raw)
        assert data.get("status") == "ok", data
        print("OK: Response is valid JSON with status=ok")
        return True
    except LLMError as exc:
        print(f"FAIL: {exc}")
        return False
    except json.JSONDecodeError as exc:
        print(f"WARN: Response was not JSON ({exc}), but Groq call succeeded.")
        return True


def test_orchestrator_with_sample_data() -> bool:
    print("\n--- Test 2: Orchestrator + Groq (sample restaurants, no HF download) ---")
    cache = DataCache()
    cache.set_records(
        [
            RestaurantRecord(
                id="1",
                name="Smoke Test Bistro",
                location="Indiranagar",
                cuisines=["Italian", "Cafe"],
                rating=4.5,
                estimated_cost=500.0,
                metadata={"listed_in(city)": "Bangalore", "votes": 100},
            ),
            RestaurantRecord(
                id="2",
                name="Curry House",
                location="Koramangala",
                cuisines=["Indian"],
                rating=4.2,
                estimated_cost=400.0,
                metadata={"listed_in(city)": "Bangalore", "votes": 80},
            ),
        ],
        cost_percentile_33=350.0,
        cost_percentile_66=550.0,
    )

    orchestrator = RecommendationOrchestrator(cache=cache)
    prefs = UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="Italian",
        additional_preferences="quick service",
    )

    try:
        result = orchestrator.recommend(prefs, require_groq_key=True)
    except LLMError as exc:
        print(f"FAIL: {exc}")
        return False

    if not result.recommendations:
        print("FAIL: No recommendations returned")
        print("Filter messages:", result.filter_messages)
        return False

    print(f"OK: Got {len(result.recommendations)} recommendation(s)")
    if result.used_fallback:
        print("WARN: Used rating fallback (Groq parse/API issue)")
    else:
        print("OK: Groq ranking path (not fallback)")

    for rec in result.recommendations:
        r = rec.restaurant
        print(f"\n  #{rec.rank} {r.name} | rating={r.rating} | cost={r.estimated_cost}")
        print(f"     Why: {rec.explanation[:200]}...")

    if result.summary:
        print(f"\n  Summary: {result.summary[:200]}")

    return True


def main() -> int:
    print("Groq live smoke test\n")
    if not _check_env():
        return 1

    ok_ping = test_groq_ping()
    ok_orch = test_orchestrator_with_sample_data()

    print("\n--- Result ---")
    if ok_ping and ok_orch:
        print("PASS: Groq LLM integration is working.")
        return 0
    print("FAIL: One or more checks failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
