"""CLI entry point for the restaurant recommendation application."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from src.models.preferences import UserPreferences
from src.services.formatter import ResultFormatter
from src.services.llm_client import LLMError
from src.services.orchestrator import OrchestratorError, RecommendationOrchestrator
from src.services.validator import PreferenceValidationError, PreferenceValidator

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zomato AI restaurant recommendation (milestone)"
    )
    parser.add_argument(
        "--load-only",
        action="store_true",
        help="Load dataset from Hugging Face, print stats and sample records",
    )
    parser.add_argument(
        "--filter",
        action="store_true",
        help="Load dataset (if needed) and filter by preferences (Phase 2)",
    )
    parser.add_argument(
        "--recommend",
        action="store_true",
        help="Full pipeline: filter + Groq recommendations (Phase 4)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output --recommend results as JSON",
    )
    parser.add_argument(
        "--location",
        help="City or area (required for --filter / --recommend)",
    )
    parser.add_argument(
        "--budget",
        choices=["low", "medium", "high", "cheap", "expensive"],
        help="Budget band (required for --filter / --recommend)",
    )
    parser.add_argument("--cuisine", help="Cuisine type (optional)")
    parser.add_argument("--min-rating", type=float, help="Minimum rating (optional)")
    parser.add_argument(
        "--additional",
        help="Additional free-text preferences (optional)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reload dataset even if cache is populated",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=3,
        help="Number of sample records to print with --load-only",
    )
    return parser


def _validate_prefs_from_args(
    args: argparse.Namespace,
) -> UserPreferences | None:
    if not args.location or not args.budget:
        print(
            "Error: --location and --budget are required",
            file=sys.stderr,
        )
        return None
    try:
        return PreferenceValidator().validate(
            location=args.location,
            budget=args.budget,
            cuisine=args.cuisine,
            min_rating=args.min_rating,
            additional_preferences=args.additional,
        )
    except PreferenceValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return None


def _run_load_only(samples: int, force: bool) -> int:
    orchestrator = RecommendationOrchestrator()
    try:
        orchestrator.ensure_data_loaded(force=force)
    except OrchestratorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    cache = orchestrator.cache
    records = cache.get_records()
    meta = cache.get_metadata()
    print(f"Loaded {len(records)} restaurant records")
    print(f"Budget percentiles: p33={meta.cost_percentile_33}, p66={meta.cost_percentile_66}")
    if meta.skipped:
        print(f"Skipped during normalization: {meta.skipped}")

    for record in records[:samples]:
        print(json.dumps(record.to_dict(), indent=2, default=str))
        print("---")

    return 0


def _run_filter(args: argparse.Namespace) -> int:
    prefs = _validate_prefs_from_args(args)
    if prefs is None:
        return 1

    orchestrator = RecommendationOrchestrator()
    try:
        orchestrator.ensure_data_loaded(force=args.force)
    except OrchestratorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    meta = orchestrator.cache.get_metadata()
    filter_result = orchestrator.filter_service.filter(
        prefs,
        orchestrator.cache.get_records(),
        cost_percentile_33=meta.cost_percentile_33,
        cost_percentile_66=meta.cost_percentile_66,
    )

    for message in filter_result.messages:
        print(f"Note: {message}")

    print(f"Candidates: {len(filter_result.candidates)}")
    for record in filter_result.candidates:
        cuisines = ", ".join(record.cuisines) if record.cuisines else "N/A"
        cost = record.estimated_cost if record.estimated_cost is not None else "N/A"
        print(
            f"  - {record.name} | {record.location} | {cuisines} | "
            f"rating={record.rating} | cost={cost}"
        )

    return 0 if filter_result.candidates else 1


def _run_recommend(args: argparse.Namespace) -> int:
    prefs = _validate_prefs_from_args(args)
    if prefs is None:
        return 1

    orchestrator = RecommendationOrchestrator()
    formatter = ResultFormatter()

    try:
        result = orchestrator.recommend(
            prefs,
            force_reload=args.force,
        )
    except OrchestratorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except LLMError as exc:
        print(f"Groq error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(formatter.format_json(result))
    else:
        print(formatter.format_cli(result))

    return 0 if result.recommendations else 1


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.load_only:
        return _run_load_only(args.samples, args.force)
    if args.recommend:
        return _run_recommend(args)
    if args.filter:
        return _run_filter(args)

    print("Commands:")
    print("  python -m src.main --load-only")
    print(
        "  python -m src.main --filter --location Bangalore --budget medium "
        "--cuisine Italian"
    )
    print(
        "  python -m src.main --recommend --location Bangalore --budget medium "
        "--cuisine Italian --additional \"family-friendly\""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
