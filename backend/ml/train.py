"""
ScamCheck ML Model Training Pipeline.

Trains a reproducible TF-IDF + Logistic Regression binary classifier on the
synthetic ML dataset with strict isolation and zero-leakage safeguards.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

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

from ml.preprocessing import batch_clean_texts


def load_ml_data(dataset_path: Path) -> Tuple[np.ndarray, np.ndarray, list]:
    """Load texts, binary labels, and raw metadata records."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    texts = np.array([r["text"] for r in records])
    labels = np.array([r["label"] for r in records])
    return texts, labels, records


def build_pipeline(
    max_features: int = 2500,
    ngram_range: Tuple[int, int] = (1, 2),
    c_param: float = 1.0,
    random_state: int = 42
) -> Pipeline:
    """Construct an end-to-end scikit-learn Pipeline with zero data leakage."""
    cleaner = FunctionTransformer(
        batch_clean_texts,
        kw_args={"normalize_entities": True},
        validate=False
    )
    
    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range,
        max_features=max_features,
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1
    )

    classifier = LogisticRegression(
        C=c_param,
        class_weight="balanced",
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


def train_model(
    dataset_path: Path,
    output_dir: Path,
    test_size: float = 0.20,
    random_state: int = 42
) -> Dict[str, Any]:
    """Execute stratified train/test split, train pipeline, and persist artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)

    texts, labels, records = load_ml_data(dataset_path)

    # Perform stratified split to maintain exact class balance across train & test
    indices = np.arange(len(texts))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=test_size,
        stratify=labels,
        random_state=random_state
    )

    X_train, y_train = texts[train_idx], labels[train_idx]
    X_test, y_test = texts[test_idx], labels[test_idx]

    print("=" * 60)
    print("SCAMCHECK ML TRAINING PIPELINE (TF-IDF + Logistic Regression)")
    print("=" * 60)
    print(f"Total dataset size:        {len(texts)}")
    print(f"Training set size:         {len(X_train)} (Scam: {np.sum(y_train == 'scam')}, Legitimate: {np.sum(y_train == 'legitimate')})")
    print(f"Test set size:             {len(X_test)} (Scam: {np.sum(y_test == 'scam')}, Legitimate: {np.sum(y_test == 'legitimate')})")
    print(f"Random Seed:               {random_state}")
    print("-" * 60)

    # Fit pipeline strictly on X_train (preventing data leakage)
    pipeline = build_pipeline(random_state=random_state)
    pipeline.fit(X_train, y_train)

    train_acc = pipeline.score(X_train, y_train)
    test_acc = pipeline.score(X_test, y_test)

    print(f"Train Accuracy:            {train_acc:.4f}")
    print(f"Test Accuracy:             {test_acc:.4f}")
    print("-" * 60)

    # Save trained model artifact
    model_file = output_dir / "scamcheck_lr_pipeline.joblib"
    joblib.dump(pipeline, model_file)
    print(f"Serialized model pipeline saved to: {model_file}")

    # Save test partition for standalone evaluation
    test_records = [records[i] for i in test_idx]
    test_file = output_dir / "test_split.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(test_records, f, indent=2)
    print(f"Held-out test partition saved to:   {test_file}")

    # Save training metadata
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(texts),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
        "random_state": random_state,
        "test_size": test_size,
        "classes": list(pipeline.classes_),
        "vocabulary_size": len(pipeline.named_steps["tfidf"].vocabulary_),
        "hyperparameters": {
            "model_type": "TF-IDF + LogisticRegression",
            "ngram_range": [1, 2],
            "max_features": 2500,
            "sublinear_tf": True,
            "C": 1.0,
            "penalty": "l2",
            "class_weight": "balanced",
            "solver": "lbfgs"
        }
    }

    meta_file = output_dir / "training_meta.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Training metadata saved to:        {meta_file}")
    print("=" * 60)

    return meta


def main():
    parser = argparse.ArgumentParser(description="Train ScamCheck TF-IDF + Logistic Regression Model")
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "data" / "ml" / "dataset.json"),
        help="Path to ML dataset JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "models"),
        help="Directory to save trained model artifacts"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    train_model(
        dataset_path=Path(args.data_path),
        output_dir=Path(args.output_dir),
        random_state=args.seed
    )


if __name__ == "__main__":
    main()
