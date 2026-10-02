"""
ScamCheck ML Dataset Validator.

Performs rigorous structural, lexical, and distributional checks on the ML dataset:
1. Field presence and type conformity.
2. Label & Category schema validity.
3. Source type correctness.
4. Exact and normalized text duplication.
5. Benchmark contamination check (ensuring no leakage with evaluation_fixture.json).
6. Near-duplicate / template repetition check.
7. Class & category distribution summaries.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set, Any


VALID_LABELS = {"scam", "legitimate"}
VALID_CATEGORIES = {"bank_payment", "fake_job", "investment", None}
VALID_SOURCE_TYPES = {"synthetic", "team_curated", "external_anonymized"}
REQUIRED_FIELDS = {"id", "text", "label", "category", "source_type", "notes"}


def jaccard_similarity(text1: str, text2: str) -> float:
    """Compute token-level Jaccard similarity between two texts."""
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)


def validate_ml_dataset(
    dataset_path: Path,
    benchmark_fixture_path: Path = None
) -> Dict[str, Any]:
    """Run full validation suite on the specified dataset file."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Dataset root must be a JSON array, got {type(data).__name__}")

    errors: List[str] = []
    warnings: List[str] = []
    
    seen_ids: Set[str] = set()
    seen_normalized_texts: Dict[str, str] = {}  # normalized_text -> id
    
    label_counts: Counter = Counter()
    category_counts: Counter = Counter()
    source_type_counts: Counter = Counter()
    label_by_category: Counter = Counter()

    # Load benchmark fixture if present to verify zero contamination
    benchmark_texts: Set[str] = set()
    if benchmark_fixture_path and benchmark_fixture_path.exists():
        with open(benchmark_fixture_path, "r", encoding="utf-8") as bf:
            bench_data = json.load(bf)
            for item in bench_data:
                norm_b = " ".join(item.get("text", "").lower().split())
                if norm_b:
                    benchmark_texts.add(norm_b)

    for idx, item in enumerate(data):
        item_loc = f"Item #{idx} (ID: {item.get('id', 'MISSING_ID')})"

        # 1. Required fields check
        missing = REQUIRED_FIELDS - set(item.keys())
        if missing:
            errors.append(f"{item_loc}: Missing required fields {missing}")

        # 2. ID validation
        item_id = item.get("id")
        if not item_id or not isinstance(item_id, str):
            errors.append(f"{item_loc}: 'id' must be a non-empty string")
        elif item_id in seen_ids:
            errors.append(f"{item_loc}: Duplicate ID '{item_id}' detected")
        else:
            seen_ids.add(item_id)

        # 3. Text validation
        text = item.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            errors.append(f"{item_loc}: 'text' must be a non-empty string")
        else:
            norm_text = " ".join(text.lower().split())
            if norm_text in seen_normalized_texts:
                errors.append(
                    f"{item_loc}: Duplicate text found (matches {seen_normalized_texts[norm_text]})"
                )
            else:
                seen_normalized_texts[norm_text] = item_id

            # Benchmark contamination check
            if norm_text in benchmark_texts:
                errors.append(
                    f"{item_loc}: Contamination warning - text identical to evaluation_fixture.json item!"
                )

        # 4. Label validation
        label = item.get("label")
        if label not in VALID_LABELS:
            errors.append(f"{item_loc}: Invalid label '{label}'. Allowed: {VALID_LABELS}")
        else:
            label_counts[label] += 1

        # 5. Category validation
        category = item.get("category")
        if category not in VALID_CATEGORIES:
            errors.append(
                f"{item_loc}: Invalid category '{category}'. Allowed: {VALID_CATEGORIES}"
            )
        else:
            cat_key = category if category is not None else "null"
            category_counts[cat_key] += 1
            label_by_category[(label, cat_key)] += 1

        # 6. Source Type validation
        source_type = item.get("source_type")
        if source_type not in VALID_SOURCE_TYPES:
            errors.append(
                f"{item_loc}: Invalid source_type '{source_type}'. Allowed: {VALID_SOURCE_TYPES}"
            )
        else:
            source_type_counts[source_type] += 1

        # 7. Notes validation
        notes = item.get("notes")
        if notes is None or not isinstance(notes, str):
            errors.append(f"{item_loc}: 'notes' must be a string description")

    # 8. Near-duplicate / Template repetition check (Jaccard > 0.85)
    text_list = [(item.get("id"), item.get("text", "")) for item in data if item.get("text")]
    high_similarity_pairs = []
    for i in range(len(text_list)):
        for j in range(i + 1, len(text_list)):
            id1, t1 = text_list[i]
            id2, t2 = text_list[j]
            sim = jaccard_similarity(t1, t2)
            if sim > 0.85:
                high_similarity_pairs.append((id1, id2, sim))

    if high_similarity_pairs:
        for id1, id2, sim in high_similarity_pairs[:5]:
            warnings.append(
                f"High lexical similarity ({sim:.2f}) between {id1} and {id2} - check template repetition."
            )
        if len(high_similarity_pairs) > 5:
            warnings.append(f"... and {len(high_similarity_pairs) - 5} more high similarity pairs.")

    summary = {
        "total_examples": len(data),
        "unique_ids": len(seen_ids),
        "unique_texts": len(seen_normalized_texts),
        "label_distribution": dict(label_counts),
        "category_distribution": dict(category_counts),
        "source_type_distribution": dict(source_type_counts),
        "breakdown": {f"{lbl}_{cat}": count for (lbl, cat), count in label_by_category.items()},
        "errors": errors,
        "warnings": warnings,
        "is_valid": len(errors) == 0,
    }

    return summary


def print_validation_report(summary: Dict[str, Any]):
    """Pretty-print the validation report to stdout."""
    print("=" * 70)
    print("SCAMCHECK ML DATASET VALIDATION REPORT")
    print("=" * 70)
    print(f"Total Examples:              {summary['total_examples']}")
    print(f"Unique IDs:                  {summary['unique_ids']}")
    print(f"Unique Normalized Texts:     {summary['unique_texts']}")
    print(f"Status:                      {'PASSED (VALID)' if summary['is_valid'] else 'FAILED'}")
    print("-" * 70)
    print("CLASS DISTRIBUTION (label):")
    for lbl, count in summary["label_distribution"].items():
        pct = (count / summary["total_examples"]) * 100
        print(f"  - {lbl:<15}: {count:>4} ({pct:>5.1f}%)")
    print("-" * 70)
    print("CATEGORY DISTRIBUTION (category):")
    for cat, count in summary["category_distribution"].items():
        pct = (count / summary["total_examples"]) * 100
        print(f"  - {cat:<15}: {count:>4} ({pct:>5.1f}%)")
    print("-" * 70)
    print("SOURCE TYPE DISTRIBUTION:")
    for src, count in summary["source_type_distribution"].items():
        pct = (count / summary["total_examples"]) * 100
        print(f"  - {src:<15}: {count:>4} ({pct:>5.1f}%)")
    print("-" * 70)
    print("DETAILED CROSS-TABULATION (Label x Category):")
    for key, count in summary["breakdown"].items():
        print(f"  - {key:<25}: {count:>4}")
    print("-" * 70)

    if summary["warnings"]:
        print(f"WARNINGS ({len(summary['warnings'])}):")
        for w in summary["warnings"]:
            print(f"  [!] {w}")
        print("-" * 70)

    if summary["errors"]:
        print(f"ERRORS ({len(summary['errors'])}):")
        for e in summary["errors"]:
            print(f"  [X] {e}")
        print("=" * 70)
    else:
        print("No errors detected. Dataset strictly complies with ML specification.")
        print("=" * 70)


def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    dataset_path = root_dir / "data" / "ml" / "dataset.json"
    benchmark_fixture_path = root_dir / "data" / "evaluation_fixture.json"

    print(f"Validating dataset: {dataset_path}")
    print(f"Cross-checking against benchmark: {benchmark_fixture_path}")
    
    summary = validate_ml_dataset(dataset_path, benchmark_fixture_path)
    print_validation_report(summary)

    if not summary["is_valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
