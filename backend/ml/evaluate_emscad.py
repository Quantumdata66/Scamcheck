"""
EMSCAD (Recruitment Scam) External Evaluation Pipeline for ScamCheck.

Evaluates trained ScamCheck ML models on the public EMSCAD dataset without retraining
or modifying models, preserving the external benchmark isolation.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import joblib
import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
    average_precision_score
)


DEFAULT_CSV_PATH = backend_dir / "data" / "external" / "emscad" / "fake_job_postings.csv"
DEFAULT_OUTPUT_DIR = backend_dir / "ml" / "results" / "emscad"


def compose_emscad_text(row: Dict[str, Any]) -> str:
    """
    Safely concatenates non-null text fields from EMSCAD without injecting 
    literal missing value tokens ('nan', 'None', 'null', 'n/a').
    """
    field_order = [
        ("Job Title", row.get("title")),
        ("Company Profile", row.get("company_profile")),
        ("Description", row.get("description")),
        ("Requirements", row.get("requirements")),
        ("Benefits", row.get("benefits")),
    ]
    
    sections = []
    for label, content in field_order:
        if content is not None:
            text_val = str(content).strip()
            # Filter out empty strings and string-encoded null representations
            if text_val and text_val.lower() not in ("nan", "none", "null", "n/a"):
                sections.append(f"{label}: {text_val}")
                
    return "\n\n".join(sections)


def map_emscad_label(fraud_val: Any) -> str:
    """Map binary fraudulent indicator to ScamCheck standard label."""
    if fraud_val is None:
        raise ValueError("Missing fraudulent label value")
    
    str_val = str(fraud_val).strip().lower()
    if str_val in ("1", "1.0", "true", "t"):
        return "scam"
    elif str_val in ("0", "0.0", "false", "f"):
        return "legitimate"
    else:
        raise ValueError(f"Invalid fraudulent label value: '{fraud_val}'")


def load_and_preprocess_emscad(csv_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load EMSCAD CSV, validate schema, compose text, and map labels.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"EMSCAD dataset file missing at expected path: {csv_path}\n"
            f"Please ensure 'fake_job_postings.csv' is placed in '{csv_path.parent}'."
        )

    records = []
    invalid_labels = 0
    empty_texts = 0
    raw_row_count = 0

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        if "fraudulent" not in (reader.fieldnames or []):
            raise KeyError(f"Required column 'fraudulent' not found in CSV headers: {reader.fieldnames}")

        for idx, row in enumerate(reader):
            raw_row_count += 1
            try:
                label = map_emscad_label(row.get("fraudulent"))
            except ValueError:
                invalid_labels += 1
                continue

            composed_text = compose_emscad_text(row)
            if not composed_text.strip():
                empty_texts += 1
                continue

            records.append({
                "job_id": row.get("job_id", f"emscad_{idx}"),
                "text": composed_text,
                "label": label,
                "source_type": "external_anonymized",
                "category": "fake_job",
                "telecommuting": row.get("telecommuting"),
                "has_company_logo": row.get("has_company_logo"),
                "has_questions": row.get("has_questions"),
                "employment_type": row.get("employment_type"),
                "required_experience": row.get("required_experience"),
                "required_education": row.get("required_education"),
                "industry": row.get("industry"),
                "function": row.get("function")
            })

    stats = {
        "raw_rows": raw_row_count,
        "valid_records": len(records),
        "invalid_labels": invalid_labels,
        "empty_texts": empty_texts
    }
    return records, stats


def deduplicate_records(
    records: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Deduplicate records based on case- and whitespace-normalized text.
    Audits whether duplicate texts have identical or conflicting labels.
    If label conflicts exist, logs them explicitly and skips ambiguous records.
    """
    from collections import defaultdict
    
    text_to_records = defaultdict(list)
    for r in records:
        norm_t = " ".join(r["text"].lower().split())
        text_to_records[norm_t].append(r)

    unique_records = []
    duplicate_count = 0
    conflicting_groups = []

    for norm_t, group in text_to_records.items():
        distinct_labels = set(r["label"] for r in group)
        if len(distinct_labels) > 1:
            # Ambiguous conflict: identical text with different ground truth labels
            conflicting_groups.append({
                "text_snippet": group[0]["text"][:150],
                "record_count": len(group),
                "labels": list(distinct_labels),
                "job_ids": [r["job_id"] for r in group]
            })
            # To prevent arbitrary selection, conflicting ambiguous texts are excluded
            continue
        
        # Valid consistent group (1 unique record + len(group)-1 duplicates)
        unique_records.append(group[0])
        if len(group) > 1:
            duplicate_count += (len(group) - 1)

    dedup_audit = {
        "raw_records": len(records),
        "unique_records": len(unique_records),
        "duplicate_instances_same_label": duplicate_count,
        "conflicting_label_groups": len(conflicting_groups),
        "conflicts": conflicting_groups
    }

    return unique_records, dedup_audit


def check_benchmark_overlap(
    records: List[Dict[str, Any]],
    synthetic_path: Path,
    benchmark_path: Path
) -> Dict[str, int]:
    """Verify zero overlap with ScamCheck synthetic dataset and benchmark fixture."""
    synthetic_texts = set()
    benchmark_texts = set()

    if synthetic_path.exists():
        with open(synthetic_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                norm = " ".join(item.get("text", "").lower().split())
                if norm:
                    synthetic_texts.add(norm)

    if benchmark_path.exists():
        with open(benchmark_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                norm = " ".join(item.get("text", "").lower().split())
                if norm:
                    benchmark_texts.add(norm)

    synth_overlap = 0
    bench_overlap = 0
    for r in records:
        norm_r = " ".join(r["text"].lower().split())
        if norm_r in synthetic_texts:
            synth_overlap += 1
        if norm_r in benchmark_texts:
            bench_overlap += 1

    return {
        "synthetic_dataset_overlap": synth_overlap,
        "evaluation_benchmark_overlap": bench_overlap
    }


def compute_metrics(
    y_true: List[str],
    y_pred: List[str],
    probas_scam: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """Compute detailed evaluation metrics with scam as positive class."""
    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=["legitimate", "scam"])
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    
    # Scam class (positive class) metrics
    prec_scam, rec_scam, f1_scam, sup_scam = precision_recall_fscore_support(
        y_true, y_pred, labels=["scam"], average=None, zero_division=0
    )
    
    # Macro F1
    macro_f1 = report["macro avg"]["f1-score"]

    # Precision-Recall AUC (PR-AUC / Average Precision) for scam class if probabilities exist
    pr_auc = None
    if probas_scam is not None:
        y_true_binary = [1 if y == "scam" else 0 for y in y_true]
        try:
            pr_auc = float(average_precision_score(y_true_binary, probas_scam))
        except Exception:
            pr_auc = None

    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "scam_metrics": {
            "precision": float(prec_scam[0]),
            "recall": float(rec_scam[0]),
            "f1": float(f1_scam[0]),
            "support": int(sup_scam[0])
        },
        "legitimate_metrics": {
            "precision": float(report["legitimate"]["precision"]),
            "recall": float(report["legitimate"]["recall"]),
            "f1": float(report["legitimate"]["f1-score"]),
            "support": int(report["legitimate"]["support"])
        },
        "macro_avg": report["macro avg"],
        "pr_auc": pr_auc,
        "confusion_matrix": {
            "true_legitimate_pred_legitimate_tn": int(cm[0][0]),
            "true_legitimate_pred_scam_fp": int(cm[0][1]),
            "true_scam_pred_legitimate_fn": int(cm[1][0]),
            "true_scam_pred_scam_tp": int(cm[1][1]),
            "matrix_array": cm.tolist()
        }
    }


def evaluate_model_pipeline(
    model_path: Path,
    records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute model inference and extract error diagnostics."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}")

    pipeline = joblib.load(model_path)
    texts = [r["text"] for r in records]
    y_true = [r["label"] for r in records]

    y_pred = pipeline.predict(texts)
    
    classes = list(pipeline.classes_) if hasattr(pipeline, "classes_") else ["legitimate", "scam"]
    scam_idx = classes.index("scam") if "scam" in classes else 1
    
    probas = pipeline.predict_proba(texts) if hasattr(pipeline, "predict_proba") else None
    probas_scam = probas[:, scam_idx] if probas is not None else None

    metrics = compute_metrics(y_true, y_pred, probas_scam)

    # Collect sample false positives (highest P_scam among true legitimate)
    # and false negatives (lowest P_scam among true scam)
    false_positives = []
    false_negatives = []

    for idx, (rec, yt, yp) in enumerate(zip(records, y_true, y_pred)):
        p_s = float(probas_scam[idx]) if probas_scam is not None else None
        item_diag = {
            "job_id": rec["job_id"],
            "title": rec["text"].split("\n")[0] if "\n" in rec["text"] else rec["text"][:80],
            "text_preview": rec["text"][:200] + ("..." if len(rec["text"]) > 200 else ""),
            "true_label": yt,
            "predicted_label": yp,
            "p_scam": p_s
        }
        if yt == "legitimate" and yp == "scam":
            false_positives.append(item_diag)
        elif yt == "scam" and yp == "legitimate":
            false_negatives.append(item_diag)

    # Sort false positives by highest P_scam descending
    false_positives.sort(key=lambda x: x["p_scam"] if x["p_scam"] is not None else 0, reverse=True)
    # Sort false negatives by lowest P_scam ascending
    false_negatives.sort(key=lambda x: x["p_scam"] if x["p_scam"] is not None else 1)

    return {
        "model_name": model_path.stem,
        "metrics": metrics,
        "sample_false_positives": false_positives[:10],
        "sample_false_negatives": false_negatives[:10],
        "total_false_positives": len(false_positives),
        "total_false_negatives": len(false_negatives),
        "all_predictions": [
            {
                "job_id": rec["job_id"],
                "true_label": yt,
                "predicted_label": yp,
                "p_scam": float(probas_scam[idx]) if probas_scam is not None else None
            }
            for idx, (rec, yt, yp) in enumerate(zip(records, y_true, y_pred))
        ]
    }


def compute_majority_baseline(y_true: List[str]) -> Dict[str, Any]:
    """Compute naive baseline that predicts all samples as legitimate."""
    y_pred_majority = ["legitimate"] * len(y_true)
    return compute_metrics(y_true, y_pred_majority, probas_scam=np.zeros(len(y_true)))


def run_emscad_evaluation(
    csv_path: Path = DEFAULT_CSV_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR
) -> Optional[Dict[str, Any]]:
    """Main evaluation runner for EMSCAD dataset."""
    print("=" * 70)
    print("SCAMCHECK EMSCAD EXTERNAL EVALUATION PIPELINE")
    print("=" * 70)

    if not csv_path.exists():
        print(f"[!] PREREQUISITE CHECK FAILED: EMSCAD CSV not found.")
        print(f"    Expected path: {csv_path}")
        print(f"    Please place 'fake_job_postings.csv' in that directory before running evaluation.")
        print("=" * 70)
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading raw EMSCAD data from: {csv_path}")
    raw_records, stats = load_and_preprocess_emscad(csv_path)
    print(f"  - Raw rows processed:      {stats['raw_rows']}")
    print(f"  - Valid composed records:  {stats['valid_records']}")
    print(f"  - Invalid labels skipped:  {stats['invalid_labels']}")
    print(f"  - Empty texts skipped:     {stats['empty_texts']}")

    print("\nDeduplicating records based on normalized text...")
    records, dedup_audit = deduplicate_records(raw_records)
    print(f"  - Unique records:                  {len(records)}")
    print(f"  - Duplicate instances (same label): {dedup_audit['duplicate_instances_same_label']}")
    print(f"  - Conflicting label groups:        {dedup_audit['conflicting_label_groups']}")
    if dedup_audit['conflicting_label_groups'] > 0:
        print(f"    [!] Warning: {dedup_audit['conflicting_label_groups']} conflicting groups excluded to prevent label corruption.")

    # Label breakdown
    y_true = [r["label"] for r in records]
    scam_count = sum(1 for y in y_true if y == "scam")
    legit_count = sum(1 for y in y_true if y == "legitimate")
    print(f"\nFinal Evaluation Distribution:")
    print(f"  - Legitimate (0):                  {legit_count} ({legit_count/len(records)*100:.2f}%)")
    print(f"  - Fraudulent / Scam (1):           {scam_count} ({scam_count/len(records)*100:.2f}%)")
    print(f"  - Total Evaluated:                 {len(records)}")

    # Overlap / Leakage audit
    synth_path = backend_dir / "data" / "ml" / "dataset.json"
    bench_path = backend_dir / "data" / "evaluation_fixture.json"
    overlap = check_benchmark_overlap(records, synth_path, bench_path)
    print(f"\nLeakage & Benchmark Isolation Audit:")
    print(f"  - Overlap with synthetic dataset (N=210): {overlap['synthetic_dataset_overlap']}")
    print(f"  - Overlap with evaluation benchmark (N=37): {overlap['evaluation_benchmark_overlap']}")

    # Majority class baseline
    majority_baseline = compute_majority_baseline(y_true)

    # Discover and evaluate available models in backend/ml/models/
    models_dir = backend_dir / "ml" / "models"
    model_files = list(models_dir.glob("*.joblib"))
    
    evaluation_results = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_source": "EMSCAD (Workable 2012-2014, Vidros et al.)",
        "csv_path": str(csv_path),
        "total_records_evaluated": len(records),
        "deduplication_audit": dedup_audit,
        "class_distribution": {
            "legitimate": legit_count,
            "scam": scam_count,
            "imbalance_ratio": f"{legit_count/max(scam_count, 1):.1f}:1"
        },
        "isolation_audit": overlap,
        "majority_class_baseline": majority_baseline,
        "models_evaluated": {}
    }

    if not model_files:
        print(f"\n[!] No trained model artifacts (.joblib) found in {models_dir}.")
    else:
        for mf in model_files:
            print(f"\nEvaluating Model Artifact: {mf.name}")
            res = evaluate_model_pipeline(mf, records)
            evaluation_results["models_evaluated"][mf.stem] = res
            
            m = res["metrics"]
            print(f"  - Accuracy:        {m['accuracy']:.4f} (Baseline: {majority_baseline['accuracy']:.4f})")
            print(f"  - Macro F1:        {m['macro_f1']:.4f}")
            print(f"  - Scam Precision:  {m['scam_metrics']['precision']:.4f}")
            print(f"  - Scam Recall:     {m['scam_metrics']['recall']:.4f}")
            print(f"  - Scam F1:         {m['scam_metrics']['f1']:.4f}")
            if m["pr_auc"] is not None:
                print(f"  - Scam PR-AUC:     {m['pr_auc']:.4f}")
            print(f"  - False Positives: {res['total_false_positives']}")
            print(f"  - False Negatives: {res['total_false_negatives']}")

    # Save structured results
    summary_file = output_dir / "emscad_evaluation_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        # Save summary without full per-record dump
        dump_copy = dict(evaluation_results)
        for k in dump_copy.get("models_evaluated", {}):
            if "all_predictions" in dump_copy["models_evaluated"][k]:
                del dump_copy["models_evaluated"][k]["all_predictions"]
        json.dump(dump_copy, f, indent=2)
    print(f"\nSummary metrics saved to: {summary_file}")

    print("=" * 70)
    return evaluation_results


def main():
    parser = argparse.ArgumentParser(description="Evaluate ScamCheck ML Models on EMSCAD Dataset")
    parser.add_argument(
        "--csv-path",
        type=str,
        default=str(DEFAULT_CSV_PATH),
        help="Path to EMSCAD fake_job_postings.csv"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to save evaluation artifacts"
    )
    args = parser.parse_args()

    run_emscad_evaluation(
        csv_path=Path(args.csv_path),
        output_dir=Path(args.output_dir)
    )


if __name__ == "__main__":
    main()
