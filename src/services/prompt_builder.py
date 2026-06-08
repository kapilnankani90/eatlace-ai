"""Build versioned LLM prompts from preferences and candidate restaurants."""

from __future__ import annotations

import json
from pathlib import Path

from src import config
from src.models.preferences import UserPreferences
from src.models.restaurant import RestaurantRecord

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "v1_system.txt"

JSON_OUTPUT_SCHEMA = """{
  "summary": "Optional one-paragraph overview for the user.",
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "Exact name from the candidate list",
      "explanation": "Why this restaurant fits the user's preferences."
    }
  ]
}"""


class PromptBuilder:
    """Construct system + user prompts for the recommendation LLM."""

    def __init__(self, prompt_version: str = "v1") -> None:
        self.prompt_version = prompt_version

    def build(
        self,
        prefs: UserPreferences,
        candidates: list[RestaurantRecord],
        *,
        top_k: int | None = None,
        strict_json: bool = False,
    ) -> tuple[str, str]:
        k = min(top_k or config.TOP_K, len(candidates))
        system = self._load_system_prompt()
        user = self._build_user_prompt(prefs, candidates, k, strict_json=strict_json)
        return system, user

    def _load_system_prompt(self) -> str:
        if SYSTEM_PROMPT_PATH.is_file():
            return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
        return (
            "You are a restaurant recommendation assistant. "
            "Use only the provided candidate restaurants. Return JSON only."
        )

    def _build_user_prompt(
        self,
        prefs: UserPreferences,
        candidates: list[RestaurantRecord],
        top_k: int,
        *,
        strict_json: bool,
    ) -> str:
        candidate_rows = [
            {
                "name": r.name,
                "location": r.location,
                "cuisines": r.cuisines,
                "rating": r.rating,
                "estimated_cost": r.estimated_cost,
            }
            for r in candidates
        ]

        prefs_json = json.dumps(prefs.to_dict(), indent=2)
        candidates_json = json.dumps(candidate_rows, indent=2)

        strict_note = (
            "\nIMPORTANT: Respond with ONLY a single JSON object. "
            "No markdown, no code fences, no extra text.\n"
            if strict_json
            else ""
        )

        return f"""{strict_note}## User preferences
{prefs_json}

## Candidate restaurants (use only these)
{candidates_json}

## Task
1. Rank the top {top_k} restaurants that best match the user preferences.
2. For each, write a personalized explanation referencing their preferences.
3. Optionally include a brief overall summary.

## Output format
Return JSON matching this schema exactly:
{JSON_OUTPUT_SCHEMA}

Use restaurant_name values exactly as they appear in the candidate list.
Do not change ratings or costs in your output; explanations only."""
