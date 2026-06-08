"""One-off script to print Hugging Face dataset schema and sample rows (task 1.1)."""

from __future__ import annotations

import json
import sys
from collections import Counter

from src import config


def main() -> int:
    try:
        from datasets import load_dataset
    except ImportError:
        print("Install dependencies: pip install -r requirements.txt", file=sys.stderr)
        return 1

    kwargs = {}
    if config.HF_TOKEN:
        kwargs["token"] = config.HF_TOKEN

    print(f"Loading {config.DATASET_ID} ...")
    dataset = load_dataset(config.DATASET_ID, **kwargs)
    split_name = "train" if "train" in dataset else list(dataset.keys())[0]
    split = dataset[split_name]

    print(f"Split: {split_name}, rows: {len(split)}")
    print("Features:", list(split.features.keys()))

    null_counts: Counter[str] = Counter()
    sample = split[0]
    print("\nFirst row sample:")
    print(json.dumps(dict(sample), indent=2, default=str)[:2000])

    check_cols = ["name", "location", "cuisines", "rate", "approx_cost(for two people)"]
    for col in check_cols:
        if col not in split.features:
            print(f"WARNING: missing column {col!r}")

    for i, row in enumerate(split):
        if i >= 5000:
            break
        for col in check_cols:
            val = row.get(col)
            if val is None or str(val).strip() in ("", "nan", "-"):
                null_counts[col] += 1

    print("\nEmpty-ish values (first 5000 rows):")
    for col in check_cols:
        print(f"  {col}: {null_counts[col]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
