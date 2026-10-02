"""
ScamCheck ML Experiment 03: EMSCAD-Trained Fake-Job Classifier Training Pipeline.

Trains and evaluates a separate binary classifier using the EMSCAD employment scam dataset.
Assesses fake-job classification on long-form vacancy postings and evaluates zero-shot
transfer to ScamCheck's short-message input domain.
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
    average_precision_score
)

from ml.preprocessing import batch_clean_texts
from ml.evaluate_emscad import compose_emscad_text, map_emscad_label, deduplicate_records


DEFAULT_CSV_PATH = backend_dir / "data" / "external" / "emscad" / "fake_job_postings.csv"
DEFAULT_BENCHMARK_PATH = backend_dir / "data" / "evaluation_fixture.json"
DEFAULT_MODELS_DIR = backend_dir / "ml" / "models"
DEFAULT_RESULTS_DIR = backend_dir / "ml" / "results" / "emscad"


def load_and_deduplicate_emscad(csv_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Load and deduplicate EMSCAD dataset records."""
    if not csv_path.exists():
        raise FileNotFoundError(f"EMSCAD CSV missing at: {csv_path}")

    raw_records = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        if "fraudulent" not in (reader.fieldnames or []):
            raise KeyError(f"Missing 'fraudulent' column in CSV: {reader.fieldnames}")

        for idx, row in enumerate(reader):
            try:
                label = map_emscad_label(row.get("fraudulent"))
            except ValueError:
                continue

            text = compose_emscad_text(row)
            if not text.strip():
                continue

            raw_records.append({
                "job_id": row.get("job_id", f"emscad_{idx}"),
                "text": text,
                "label": label,
                "category": "fake_job",
                "source_type": "external_anonymized",
                "title": row.get("title", "")
            })

    unique_records, dedup_audit = deduplicate_records(raw_records)
    return unique_records, dedup_audit


def create_stratified_splits(
    records: List[Dict[str, Any]],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Split deduplicated records into Train (70%), Validation (15%), and Test (15%) partitions
    stratified by target label.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Split ratios must sum to 1.0"

    indices = np.arange(len(records))
    labels = np.array([r["label"] for r in records])

    # First split: Train (70%) vs Temp (30%)
    temp_size = val_ratio + test_ratio
    train_idx, temp_idx = train_test_split(
        indices,
        test_size=temp_size,
        stratify=labels,
        random_state=random_state
    )

    # Second split: Temp (30%) into Val (15%) and Test (15%) -> equal 50/50 split of temp
    temp_labels = labels[temp_idx]
    val_idx_rel, test_idx_rel = train_test_split(
        np.arange(len(temp_idx)),
        test_size=0.50,
        stratify=temp_labels,
        random_state=random_state
    )
    val_idx = temp_idx[val_idx_rel]
    test_idx = temp_idx[test_idx_rel]

    train_records = [records[i] for i in train_idx]
    val_records = [records[i] for i in val_idx]
    test_records = [records[i] for i in test_idx]

    # Verify no partition intersection
    assert set(train_idx).isdisjoint(set(val_idx)), "Train and Val overlap detected!"
    assert set(train_idx).isdisjoint(set(test_idx)), "Train and Test overlap detected!"
    assert set(val_idx).isdisjoint(set(test_idx)), "Val and Test overlap detected!"

    # Verify normalized texts do not cross partitions
    train_texts = set(" ".join(r["text"].lower().split()) for r in train_records)
    val_texts = set(" ".join(r["text"].lower().split()) for r in val_records)
    test_texts = set(" ".join(r["text"].lower().split()) for r in test_records)

    assert train_texts.isdisjoint(val_texts), "Data leakage: Train and Val share normalized texts!"
    assert train_texts.isdisjoint(test_texts), "Data leakage: Train and Test share normalized texts!"
    assert val_texts.isdisjoint(test_texts), "Data leakage: Val and Test share normalized texts!"

    split_manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "random_state": random_state,
        "total_unique_records": len(records),
        "split_ratios": {
            "train": train_ratio,
            "validation": val_ratio,
            "test": test_ratio
        },
        "counts": {
            "train": {
                "total": len(train_records),
                "scam": sum(1 for r in train_records if r["label"] == "scam"),
                "legitimate": sum(1 for r in train_records if r["label"] == "legitimate")
            },
            "validation": {
                "total": len(val_records),
                "scam": sum(1 for r in val_records if r["label"] == "scam"),
                "legitimate": sum(1 for r in val_records if r["label"] == "legitimate")
            },
            "test": {
                "total": len(test_records),
                "scam": sum(1 for r in test_records if r["label"] == "scam"),
                "legitimate": sum(1 for r in test_records if r["label"] == "legitimate")
            }
        },
        "train_job_ids": [r["job_id"] for r in train_records],
        "validation_job_ids": [r["job_id"] for r in val_records],
        "test_job_ids": [r["job_id"] for r in test_records]
    }

    return train_records, val_records, test_records, split_manifest


def build_pipeline(
    analyzer: str = "word",
    ngram_range: Tuple[int, int] = (1, 2),
    max_features: int = 10000,
    sublinear_tf: bool = True,
    c_param: float = 1.0,
    class_weight: Optional[str] = "balanced",
    random_state: int = 42
) -> Pipeline:
    """Build scikit-learn Pipeline with preprocessing, vectorization, and logistic regression."""
    cleaner = FunctionTransformer(
        batch_clean_texts,
        kw_args={"normalize_entities": True},
        validate=False
    )

    vectorizer = TfidfVectorizer(
        analyzer=analyzer,
        ngram_range=ngram_range,
        max_features=max_features,
        sublinear_tf=sublinear_tf,
        strip_accents="unicode",
        min_df=2
    )

    classifier = LogisticRegression(
        C=c_param,
        class_weight=class_weight,
        solver="lbfgs",
        max_iter=1000,
        random_state=random_state
    )

    pipeline = Pipeline([
        ("preprocessor", cleaner),
        ("tfidf", vectorizer),
        ("classifier", classifier)
    ])

    return pipeline


def evaluate_partition(
    pipeline: Pipeline,
    records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate comprehensive classification metrics on a dataset partition."""
    texts = [r["text"] for r in records]
    y_true = [r["label"] for r in records]
    classes = list(pipeline.classes_)
    scam_idx = classes.index("scam")

    y_pred = pipeline.predict(texts)
    y_proba = pipeline.predict_proba(texts)
    p_scam = y_proba[:, scam_idx]

    y_true_binary = np.array([1 if y == "scam" else 0 for y in y_true])
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, sup = precision_recall_fscore_support(y_true, y_pred, labels=["legitimate", "scam"], zero_division=0)
    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)

    try:
        pr_auc = float(average_precision_score(y_true_binary, p_scam))
    except Exception:
        pr_auc = 0.0

    cm = confusion_matrix(y_true, y_pred, labels=["legitimate", "scam"])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "macro_precision": float(macro_prec),
        "macro_recall": float(macro_rec),
        "scam_precision": float(prec[1]),
        "scam_recall": float(rec[1]),
        "scam_f1": float(f1[1]),
        "scam_support": int(sup[1]),
        "legitimate_precision": float(prec[0]),
        "legitimate_recall": float(rec[0]),
        "legitimate_f1": float(f1[0]),
        "legitimate_support": int(sup[0]),
        "pr_auc": float(pr_auc),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "matrix": cm.tolist()
        }
    }


def run_model_selection(
    train_records: List[Dict[str, Any]],
    val_records: List[Dict[str, Any]],
    random_state: int = 42
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Train and evaluate a small grid of sensible candidate configurations on the Validation split.
    Validation criteria: Scam PR-AUC and Macro F1 on the held-out Validation set.
    """
    candidates = [
        {
            "config_id": "CONFIG_01_WORD_TFIDF_C1_BALANCED",
            "name": "Word TF-IDF (1-2), max_feat=10k, C=1.0, balanced",
            "params": {
                "analyzer": "word",
                "ngram_range": (1, 2),
                "max_features": 10000,
                "c_param": 1.0,
                "class_weight": "balanced",
                "sublinear_tf": True
            }
        },
        {
            "config_id": "CONFIG_02_WORD_TFIDF_C05_BALANCED",
            "name": "Word TF-IDF (1-2), max_feat=10k, C=0.5 (Stronger L2), balanced",
            "params": {
                "analyzer": "word",
                "ngram_range": (1, 2),
                "max_features": 10000,
                "c_param": 0.5,
                "class_weight": "balanced",
                "sublinear_tf": True
            }
        },
        {
            "config_id": "CONFIG_03_WORD_TFIDF_C2_BALANCED",
            "name": "Word TF-IDF (1-2), max_feat=10k, C=2.0 (Weaker L2), balanced",
            "params": {
                "analyzer": "word",
                "ngram_range": (1, 2),
                "max_features": 10000,
                "c_param": 2.0,
                "class_weight": "balanced",
                "sublinear_tf": True
            }
        },
        {
            "config_id": "CONFIG_04_WORD_UNIGRAM_C1_BALANCED",
            "name": "Word TF-IDF (1-1) Unigram, max_feat=10k, C=1.0, balanced",
            "params": {
                "analyzer": "word",
                "ngram_range": (1, 1),
                "max_features": 10000,
                "c_param": 1.0,
                "class_weight": "balanced",
                "sublinear_tf": True
            }
        },
        {
            "config_id": "CONFIG_05_CHAR_WB_TFIDF_C1_BALANCED",
            "name": "Char-WB TF-IDF (3-4), max_feat=5k, C=1.0, balanced",
            "params": {
                "analyzer": "char_wb",
                "ngram_range": (3, 4),
                "max_features": 5000,
                "c_param": 1.0,
                "class_weight": "balanced",
                "sublinear_tf": True
            }
        }
    ]

    train_texts = [r["text"] for r in train_records]
    train_labels = [r["label"] for r in train_records]

    validation_results = []
    best_config = None
    best_score = -1.0

    print("Executing Model Selection on Validation Partition (N=2,430)...")
    for cand in candidates:
        pipeline = build_pipeline(
            analyzer=cand["params"]["analyzer"],
            ngram_range=cand["params"]["ngram_range"],
            max_features=cand["params"]["max_features"],
            sublinear_tf=cand["params"]["sublinear_tf"],
            c_param=cand["params"]["c_param"],
            class_weight=cand["params"]["class_weight"],
            random_state=random_state
        )

        # Fit strictly on train partition
        pipeline.fit(train_texts, train_labels)

        # Evaluate on validation partition
        val_metrics = evaluate_partition(pipeline, val_records)
        
        # Primary selection metric: Macro F1 + PR-AUC composite
        selection_score = val_metrics["macro_f1"] + val_metrics["pr_auc"]

        record = {
            "config_id": cand["config_id"],
            "name": cand["name"],
            "hyperparameters": cand["params"],
            "validation_metrics": val_metrics,
            "selection_score": float(selection_score)
        }
        validation_results.append(record)

        print(f"  - {cand['config_id']}: Val Macro-F1={val_metrics['macro_f1']:.4f}, Scam-F1={val_metrics['scam_f1']:.4f}, PR-AUC={val_metrics['pr_auc']:.4f}, Score={selection_score:.4f}")

        if selection_score > best_score:
            best_score = selection_score
            best_config = cand

    print(f"Selected Best Configuration: {best_config['config_id']} (Score: {best_score:.4f})")
    return best_config, validation_results


def evaluate_short_message_benchmark(
    pipeline: Pipeline,
    fixture_path: Path
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Evaluate trained pipeline on the isolated 37-example short-message benchmark.
    Uses documented binary mapping: 'high' / 'needs_verification' -> scam, 'low' -> legitimate.
    """
    if not fixture_path.exists():
        raise FileNotFoundError(f"Benchmark fixture not found: {fixture_path}")

    with open(fixture_path, "r", encoding="utf-8") as f:
        benchmark_items = json.load(f)

    predictions = []
    classes = list(pipeline.classes_)
    scam_idx = classes.index("scam")

    for item in benchmark_items:
        text = item["text"]
        expected_tier = item["expected_label"]
        source_type = item.get("source_type", "")
        mapped_true = "scam" if expected_tier in ("high", "needs_verification") else "legitimate"

        y_pred = pipeline.predict([text])[0]
        y_proba = pipeline.predict_proba([text])[0]
        p_scam = float(y_proba[scam_idx])

        is_correct = (y_pred == mapped_true)
        predictions.append({
            "id": item["id"],
            "text": text,
            "expected_tier": expected_tier,
            "source_type": source_type,
            "mapped_true_label": mapped_true,
            "predicted_label": y_pred,
            "p_scam": p_scam,
            "is_correct": is_correct
        })

    # Metrics computation
    y_true = [p["mapped_true_label"] for p in predictions]
    y_pred = [p["predicted_label"] for p in predictions]
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, sup = precision_recall_fscore_support(y_true, y_pred, labels=["legitimate", "scam"], zero_division=0)
    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)

    # Adversarial subset vs Standard subset (13 items vs 24 items)
    adversarial_items = [p for p in predictions if p["id"].startswith("ADVERSARIAL_")]
    standard_items = [p for p in predictions if not p["id"].startswith("ADVERSARIAL_")]

    adv_acc = sum(1 for p in adversarial_items if p["is_correct"]) / len(adversarial_items) if adversarial_items else 0.0
    std_acc = sum(1 for p in standard_items if p["is_correct"]) / len(standard_items) if standard_items else 0.0

    metrics = {
        "overall": {
            "total_samples": len(predictions),
            "accuracy": float(acc),
            "macro_f1": float(macro_f1),
            "macro_precision": float(macro_prec),
            "macro_recall": float(macro_rec),
            "scam_precision": float(prec[1]),
            "scam_recall": float(rec[1]),
            "scam_f1": float(f1[1]),
            "scam_support": int(sup[1]),
            "legitimate_precision": float(prec[0]),
            "legitimate_recall": float(rec[0]),
            "legitimate_f1": float(f1[0]),
            "legitimate_support": int(sup[0])
        },
        "subsets": {
            "adversarial_count": len(adversarial_items),
            "adversarial_correct": sum(1 for p in adversarial_items if p["is_correct"]),
            "adversarial_accuracy": float(adv_acc),
            "standard_count": len(standard_items),
            "standard_correct": sum(1 for p in standard_items if p["is_correct"]),
            "standard_accuracy": float(std_acc)
        }
    }

    return metrics, predictions


def main():
    parser = argparse.ArgumentParser(description="ScamCheck Experiment 03: EMSCAD Training Pipeline")
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV_PATH, help="Path to fake_job_postings.csv")
    parser.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS_DIR, help="Directory to save models")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR, help="Directory to save results")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    args.models_dir.mkdir(parents=True, exist_ok=True)
    args.results_dir.mkdir(parents=True, exist_ok=True)

    print("======================================================================")
    print("SCAMCHECK ML EXPERIMENT 03: EMSCAD FAKE-JOB CLASSIFIER")
    print("======================================================================")

    # 1. Load and deduplicate
    print(f"Loading and deduplicating EMSCAD from: {args.csv_path}")
    unique_records, dedup_audit = load_and_deduplicate_emscad(args.csv_path)
    print(f"  - Unique records: {len(unique_records)} (duplicates removed: {dedup_audit['duplicate_instances_same_label']})")
    print(f"  - Conflicting label groups: {dedup_audit['conflicting_label_groups']}")

    # 2. Stratified split (70 / 15 / 15)
    print("\nCreating Stratified Train (70%), Validation (15%), and Test (15%) splits...")
    train_records, val_records, test_records, split_manifest = create_stratified_splits(
        unique_records,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=args.seed
    )
    print(f"  - Train Partition:      {len(train_records)} (Scam: {split_manifest['counts']['train']['scam']}, Legit: {split_manifest['counts']['train']['legitimate']})")
    print(f"  - Validation Partition: {len(val_records)} (Scam: {split_manifest['counts']['validation']['scam']}, Legit: {split_manifest['counts']['validation']['legitimate']})")
    print(f"  - Test Partition:       {len(test_records)} (Scam: {split_manifest['counts']['test']['scam']}, Legit: {split_manifest['counts']['test']['legitimate']})")

    # Save split manifest
    manifest_path = args.models_dir / "emscad_splits.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(split_manifest, f, indent=2)
    print(f"Saved split manifest to: {manifest_path}")

    # 3. Model selection on validation partition
    best_config, val_results = run_model_selection(train_records, val_records, random_state=args.seed)

    val_metrics_path = args.results_dir / "emscad_validation_metrics.json"
    with open(val_metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "selected_config": best_config["config_id"],
            "candidate_results": val_results
        }, f, indent=2)
    print(f"Saved validation metrics to: {val_metrics_path}")

    # 4. Fit winning pipeline on training partition
    print(f"\nTraining winning pipeline ({best_config['config_id']}) on Training Partition (N={len(train_records)})...")
    pipeline = build_pipeline(
        analyzer=best_config["params"]["analyzer"],
        ngram_range=best_config["params"]["ngram_range"],
        max_features=best_config["params"]["max_features"],
        sublinear_tf=best_config["params"]["sublinear_tf"],
        c_param=best_config["params"]["c_param"],
        class_weight=best_config["params"]["class_weight"],
        random_state=args.seed
    )

    train_texts = [r["text"] for r in train_records]
    train_labels = [r["label"] for r in train_records]
    pipeline.fit(train_texts, train_labels)

    # Persist model pipeline
    model_artifact_path = args.models_dir / "scamcheck_emscad_fake_job_pipeline.joblib"
    joblib.dump(pipeline, model_artifact_path)
    print(f"Saved model pipeline artifact to: {model_artifact_path}")

    # 5. Evaluate on held-out test partition
    print("\nEvaluating on Held-Out Test Partition (N=2,431)...")
    test_metrics = evaluate_partition(pipeline, test_records)

    # Compute detailed test predictions and false positive/negative samples
    test_texts = [r["text"] for r in test_records]
    classes = list(pipeline.classes_)
    scam_idx = classes.index("scam")
    test_preds = pipeline.predict(test_texts)
    test_probas = pipeline.predict_proba(test_texts)[:, scam_idx]

    test_predictions_list = []
    fps = []
    fns = []

    for i, r in enumerate(test_records):
        y_true = r["label"]
        y_pred = test_preds[i]
        p_scam = float(test_probas[i])
        is_correct = (y_true == y_pred)

        pred_item = {
            "job_id": r["job_id"],
            "title": r.get("title", ""),
            "text_preview": r["text"][:200] + ("..." if len(r["text"]) > 200 else ""),
            "true_label": y_true,
            "predicted_label": y_pred,
            "p_scam": p_scam,
            "is_correct": is_correct
        }
        test_predictions_list.append(pred_item)

        if y_true == "legitimate" and y_pred == "scam":
            fps.append(pred_item)
        elif y_true == "scam" and y_pred == "legitimate":
            fns.append(pred_item)

    # Save test predictions
    test_pred_path = args.models_dir / "emscad_test_predictions.json"
    with open(test_pred_path, "w", encoding="utf-8") as f:
        json.dump(test_predictions_list, f, indent=2)
    print(f"Saved test predictions to: {test_pred_path}")

    # 6. Evaluate on short-message diagnostic benchmark
    print("\nEvaluating on 37-Example Short-Message Benchmark Diagnostic...")
    benchmark_metrics, benchmark_preds = evaluate_short_message_benchmark(pipeline, DEFAULT_BENCHMARK_PATH)
    benchmark_pred_path = args.models_dir / "benchmark_predictions_emscad.json"
    with open(benchmark_pred_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_preds, f, indent=2)
    print(f"Saved benchmark predictions to: {benchmark_pred_path}")

    # 7. Compile and save Experiment 03 summary metadata
    training_meta = {
        "experiment_id": "EXP-03-EMSCAD-FAKE-JOB",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_artifact": str(model_artifact_path.name),
        "random_state": args.seed,
        "selected_configuration": best_config,
        "split_counts": split_manifest["counts"],
        "test_metrics": test_metrics,
        "majority_class_test_baseline": {
            "accuracy": test_metrics["legitimate_support"] / len(test_records),
            "scam_precision": 0.0,
            "scam_recall": 0.0,
            "scam_f1": 0.0,
            "pr_auc": test_metrics["scam_support"] / len(test_records)
        },
        "sample_false_positives": fps[:10],
        "sample_false_negatives": fns[:10],
        "total_false_positives": len(fps),
        "total_false_negatives": len(fns),
        "short_message_benchmark_transfer": benchmark_metrics
    }

    meta_path = args.models_dir / "training_meta_emscad.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(training_meta, f, indent=2)
    print(f"Saved training metadata to: {meta_path}")

    print("\n======================================================================")
    print("FINAL EXPERIMENT 03 RESULTS SUMMARY")
    print("======================================================================")
    print(f"Model Artifact:    {model_artifact_path.name}")
    print(f"Test Accuracy:     {test_metrics['accuracy']:.4f} (Majority Baseline: {training_meta['majority_class_test_baseline']['accuracy']:.4f})")
    print(f"Test Macro F1:     {test_metrics['macro_f1']:.4f}")
    print(f"Test Scam Prec:    {test_metrics['scam_precision']:.4f}")
    print(f"Test Scam Recall:  {test_metrics['scam_recall']:.4f}")
    print(f"Test Scam F1:      {test_metrics['scam_f1']:.4f}")
    print(f"Test Scam PR-AUC:  {test_metrics['pr_auc']:.4f}")
    print(f"Test Confusion:    TN={test_metrics['confusion_matrix']['tn']}, FP={test_metrics['confusion_matrix']['fp']}, FN={test_metrics['confusion_matrix']['fn']}, TP={test_metrics['confusion_matrix']['tp']}")
    print(f"Benchmark Diagnostic (37 examples): Accuracy={benchmark_metrics['overall']['accuracy']:.4f}, Macro-F1={benchmark_metrics['overall']['macro_f1']:.4f}, Adv Acc={benchmark_metrics['subsets']['adversarial_accuracy']:.4f}")
    print("======================================================================")


if __name__ == "__main__":
    main()
