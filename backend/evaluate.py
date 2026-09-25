"""
Evaluation and error analysis runner for ScamCheck baseline detector.
Evaluates detector performance against the labelled evaluation fixture.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict

from app.services.detector import RulesBaselineDetector


def load_fixture(fixture_path: Path) -> List[Dict[str, Any]]:
    """Load evaluation examples from JSON fixture."""
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_metrics(y_true: List[str], y_pred: List[str], labels: List[str]) -> Dict[str, Any]:
    """Calculate confusion matrix, precision, recall, and F1 for multi-class predictions."""
    matrix = {true_lbl: {pred_lbl: 0 for pred_lbl in labels} for true_lbl in labels}
    for true_val, pred_val in zip(y_true, y_pred):
        if true_val in matrix and pred_val in matrix[true_val]:
            matrix[true_val][pred_val] += 1

    per_class = {}
    for lbl in labels:
        tp = matrix[lbl][lbl]
        fp = sum(matrix[other][lbl] for other in labels if other != lbl)
        fn = sum(matrix[lbl][other] for other in labels if other != lbl)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[lbl] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "support": sum(matrix[lbl].values()),
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3),
        }

    # Macro averages
    macro_prec = sum(c["precision"] for c in per_class.values()) / len(labels)
    macro_rec = sum(c["recall"] for c in per_class.values()) / len(labels)
    macro_f1 = sum(c["f1"] for c in per_class.values()) / len(labels)

    return {
        "confusion_matrix": matrix,
        "per_class": per_class,
        "macro_avg": {
            "precision": round(macro_prec, 3),
            "recall": round(macro_rec, 3),
            "f1": round(macro_f1, 3),
        }
    }


def run_evaluation():
    """Execute evaluation against the fixture and print comprehensive audit."""
    fixture_file = Path(__file__).parent / "data" / "evaluation_fixture.json"
    if not fixture_file.exists():
        print(f"Error: Fixture file not found at {fixture_file}")
        return

    data = load_fixture(fixture_file)
    detector = RulesBaselineDetector()

    total = len(data)
    label_correct = 0
    cat_correct = 0

    y_true_labels = []
    y_pred_labels = []

    false_positives = []
    false_negatives = []
    category_mismatches = []
    other_discrepancies = []

    source_type_stats = defaultdict(lambda: {"total": 0, "correct_label": 0})

    for item in data:
        item_id = item["id"]
        text = item["text"]
        exp_label = item["expected_label"]
        exp_cat = item["expected_category"]
        source_type = item.get("source_type", "unknown")

        response = detector.analyze(text)
        pred_label = response.risk_level
        pred_cat = response.category

        y_true_labels.append(exp_label)
        y_pred_labels.append(pred_label)

        source_type_stats[source_type]["total"] += 1
        is_label_match = (pred_label == exp_label)
        is_cat_match = (pred_cat == exp_cat)

        if is_label_match:
            label_correct += 1
            source_type_stats[source_type]["correct_label"] += 1

        if is_cat_match:
            cat_correct += 1

        # Check error types
        if exp_label == "low" and pred_label != "low":
            false_positives.append({
                "id": item_id,
                "text": text,
                "expected_label": exp_label,
                "pred_label": pred_label,
                "indicators": response.indicators,
                "notes": item.get("notes", "")
            })
        elif exp_label in ["needs_verification", "high"] and pred_label == "low":
            false_negatives.append({
                "id": item_id,
                "text": text,
                "expected_label": exp_label,
                "pred_label": pred_label,
                "expected_cat": exp_cat,
                "notes": item.get("notes", "")
            })
        elif not is_cat_match and exp_cat is not None:
            category_mismatches.append({
                "id": item_id,
                "text": text,
                "expected_cat": exp_cat,
                "pred_cat": pred_cat,
                "indicators": response.indicators,
                "notes": item.get("notes", "")
            })
        elif not is_label_match:
            other_discrepancies.append({
                "id": item_id,
                "text": text,
                "expected_label": exp_label,
                "pred_label": pred_label,
                "indicators": response.indicators,
                "notes": item.get("notes", "")
            })

    labels = ["low", "needs_verification", "high"]
    metrics = calculate_metrics(y_true_labels, y_pred_labels, labels)

    print("=" * 70)
    print("SCAMCHECK BASELINE DETECTOR — EVALUATION REPORT")
    print("=" * 70)
    print(f"Total Fixture Examples: {total}")
    print(f"Label Accuracy: {label_correct}/{total} ({label_correct/total*100:.1f}%)")
    print(f"Category Accuracy: {cat_correct}/{total} ({cat_correct/total*100:.1f}%)")
    print()

    print("--- PERFORMANCE BY SOURCE TYPE ---")
    for stype, stats in source_type_stats.items():
        st_total = stats["total"]
        st_corr = stats["correct_label"]
        print(f"  • {stype}: {st_corr}/{st_total} ({st_corr/st_total*100:.1f}%)")
    print()

    print("--- CONFUSION MATRIX (Risk Levels) ---")
    header = f"{'True / Pred':<20}" + "".join([f"{lbl:<20}" for lbl in labels])
    print(header)
    print("-" * len(header))
    for true_lbl in labels:
        row = f"{true_lbl:<20}" + "".join([f"{metrics['confusion_matrix'][true_lbl][p_lbl]:<20}" for p_lbl in labels])
        print(row)
    print()

    print("--- CLASSIFICATION METRICS (Per Risk Tier) ---")
    for lbl, vals in metrics["per_class"].items():
        print(f"  [{lbl.upper()}] (Support: {vals['support']})")
        print(f"    Precision: {vals['precision']} | Recall: {vals['recall']} | F1-Score: {vals['f1']}")
    print()
    print(f"Macro Average — Precision: {metrics['macro_avg']['precision']}, Recall: {metrics['macro_avg']['recall']}, F1: {metrics['macro_avg']['f1']}")
    print()

    print("=" * 70)
    print("DETAILED ERROR AUDIT")
    print("=" * 70)
    print(f"False Positives (Clean marked as suspicious): {len(false_positives)}")
    for fp in false_positives:
        print(f"  - [{fp['id']}] Pred: {fp['pred_label']} (Exp: {fp['expected_label']})")
        print(f"    Text: \"{fp['text']}\"")
        print(f"    Triggered Indicators: {fp['indicators']}")
        print(f"    Notes: {fp['notes']}")
        print()

    print(f"False Negatives (Suspicious marked as Low): {len(false_negatives)}")
    for fn in false_negatives:
        print(f"  - [{fn['id']}] Pred: {fn['pred_label']} (Exp: {fn['expected_label']}, Cat: {fn['expected_cat']})")
        print(f"    Text: \"{fn['text']}\"")
        print(f"    Notes: {fn['notes']}")
        print()

    print(f"Category Mismatches: {len(category_mismatches)}")
    for cm in category_mismatches:
        print(f"  - [{cm['id']}] Pred Cat: {cm['pred_cat']} (Exp Cat: {cm['expected_cat']})")
        print(f"    Text: \"{cm['text']}\"")
        print(f"    Triggered Indicators: {cm['indicators']}")
        print(f"    Notes: {cm['notes']}")
        print()

    print(f"Other Label Discrepancies (e.g. High vs Needs_Verification): {len(other_discrepancies)}")
    for od in other_discrepancies:
        print(f"  - [{od['id']}] Pred: {od['pred_label']} (Exp: {od['expected_label']})")
        print(f"    Text: \"{od['text']}\"")
        print(f"    Triggered Indicators: {od['indicators']}")
        print(f"    Notes: {od['notes']}")
        print()

    return {
        "total": total,
        "label_correct": label_correct,
        "cat_correct": cat_correct,
        "metrics": metrics,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "category_mismatches": category_mismatches,
        "other_discrepancies": other_discrepancies
    }


if __name__ == "__main__":
    run_evaluation()
