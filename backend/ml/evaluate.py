"""
ScamCheck ML Model Evaluation Script.

Evaluates a trained model pipeline against:
1. The held-out synthetic test partition.
2. The isolated 37-example evaluation benchmark fixture.

Computes precision, recall, f1-score, confusion matrix, and provides per-sample diagnostics.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import joblib
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score


def evaluate_on_dataset(
    model_pipeline,
    records: List[Dict[str, Any]],
    dataset_name: str = "Test Set"
) -> Dict[str, Any]:
    """Run model inference and generate comprehensive evaluation metrics."""
    texts = [r["text"] for r in records]
    
    # Handle label mapping for evaluation fixture if necessary
    y_true = []
    for r in records:
        if "label" in r:
            y_true.append(r["label"])
        elif "expected_label" in r:
            # Map rule risk tiers to binary label
            # 'high' & 'needs_verification' are suspicious/scam; 'low' is legitimate/benign
            mapped = "scam" if r["expected_label"] in ("high", "needs_verification") else "legitimate"
            y_true.append(mapped)
        else:
            raise KeyError(f"No valid label found in record: {r.get('id')}")

    y_pred = model_pipeline.predict(texts)
    
    # Extract prediction probabilities if classifier supports predict_proba
    has_proba = hasattr(model_pipeline, "predict_proba")
    probas = model_pipeline.predict_proba(texts) if has_proba else None
    classes = list(model_pipeline.classes_) if hasattr(model_pipeline, "classes_") else ["legitimate", "scam"]
    scam_idx = classes.index("scam") if "scam" in classes else 1

    acc = accuracy_score(y_true, y_pred)
    report_dict = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=["legitimate", "scam"])

    # Collect misclassified samples for error analysis
    misclassifications = []
    for idx, (rec, yt, yp) in enumerate(zip(records, y_true, y_pred)):
        if yt != yp:
            p_scam = float(probas[idx][scam_idx]) if has_proba else None
            misclassifications.append({
                "id": rec.get("id", f"sample_{idx}"),
                "text": rec.get("text", ""),
                "true_label": yt,
                "predicted_label": yp,
                "p_scam": p_scam,
                "category": rec.get("category") or rec.get("expected_category"),
                "notes": rec.get("notes", "")
            })

    print("=" * 70)
    print(f"EVALUATION RESULTS: {dataset_name} (N={len(records)})")
    print("=" * 70)
    print(f"Accuracy:                    {acc:.4f} ({np.sum(np.array(y_true) == y_pred)}/{len(y_true)})")
    print("-" * 70)
    print(f"{'Class':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<8}")
    print("-" * 70)
    for cls in ["legitimate", "scam"]:
        if cls in report_dict:
            metrics = report_dict[cls]
            print(f"{cls:<15} {metrics['precision']:<12.4f} {metrics['recall']:<12.4f} {metrics['f1-score']:<12.4f} {metrics['support']:<8}")
    print("-" * 70)
    macro = report_dict["macro avg"]
    print(f"{'Macro Avg':<15} {macro['precision']:<12.4f} {macro['recall']:<12.4f} {macro['f1-score']:<12.4f} {macro['support']:<8}")
    print("-" * 70)
    print("CONFUSION MATRIX (Rows: True [legit, scam], Cols: Pred [legit, scam]):")
    print(f"  [[Legit->Legit: {cm[0][0]:<3}  Legit->Scam: {cm[0][1]:<3}]")
    print(f"   [Scam->Legit:  {cm[1][0]:<3}  Scam->Scam:  {cm[1][1]:<3}]]")
    print("-" * 70)
    print(f"Misclassified Count:         {len(misclassifications)}")
    if misclassifications:
        print("\nMISCLASSIFIED SAMPLES:")
        for m in misclassifications:
            p_str = f"(P_scam: {m['p_scam']:.3f})" if m['p_scam'] is not None else ""
            print(f"  - [{m['id']}] True: {m['true_label']} | Pred: {m['predicted_label']} {p_str}")
            print(f"    Text: \"{m['text']}\"")
            print(f"    Notes: {m['notes']}")
    print("=" * 70)

    return {
        "dataset_name": dataset_name,
        "sample_count": len(records),
        "accuracy": float(acc),
        "classification_report": report_dict,
        "confusion_matrix": cm.tolist(),
        "misclassifications": misclassifications
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate ScamCheck ML Model")
    parser.add_argument(
        "--model-path",
        type=str,
        default=str(Path(__file__).resolve().parent / "models" / "scamcheck_lr_pipeline.joblib"),
        help="Path to trained model pipeline (.joblib)"
    )
    parser.add_argument(
        "--test-split",
        type=str,
        default=str(Path(__file__).resolve().parent / "models" / "test_split.json"),
        help="Path to held-out test split JSON"
    )
    parser.add_argument(
        "--benchmark-fixture",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "data" / "evaluation_fixture.json"),
        help="Path to 37-example external benchmark fixture"
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=str(Path(__file__).resolve().parent / "models" / "evaluation_report.json"),
        help="Path to save evaluation summary JSON"
    )
    args = parser.parse_args()

    model_path = Path(args.model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}. Run train.py first.")

    pipeline = joblib.load(model_path)
    reports = {}

    # 1. Evaluate on held-out test partition if available
    test_split_path = Path(args.test_split)
    if test_split_path.exists():
        with open(test_split_path, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        reports["held_out_test_split"] = evaluate_on_dataset(
            pipeline, test_data, dataset_name="Held-Out Synthetic Test Partition"
        )

    # 2. Evaluate on external benchmark fixture if available
    bench_path = Path(args.benchmark_fixture)
    if bench_path.exists():
        with open(bench_path, "r", encoding="utf-8") as f:
            bench_data = json.load(f)
        reports["external_benchmark_fixture"] = evaluate_on_dataset(
            pipeline, bench_data, dataset_name="Isolated Benchmark Fixture (evaluation_fixture.json)"
        )

    # Save summary report
    out_path = Path(args.output_report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)
    print(f"\nFull evaluation report saved to: {out_path}")


if __name__ == "__main__":
    main()
