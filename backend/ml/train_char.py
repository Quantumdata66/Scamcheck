"""
ScamCheck ML Experiment 02: Character-Level TF-IDF + Logistic Regression Training Pipeline.

Trains a character n-gram (char_wb 3-5) classifier using the exact same train/test split
and random seed (42) as Experiment 01 to evaluate subword robustness against adversarial perturbations.
"""

import argparse
import json
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


def build_char_pipeline(
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (3, 5),
    c_param: float = 1.0,
    random_state: int = 42
) -> Pipeline:
    """Construct a character-level TF-IDF + Logistic Regression pipeline."""
    cleaner = FunctionTransformer(
        batch_clean_texts,
        kw_args={"normalize_entities": True},
        validate=False
    )
    
    # Character n-grams with word boundary awareness (char_wb)
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
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


def train_char_model(
    dataset_path: Path,
    output_dir: Path,
    test_size: float = 0.20,
    random_state: int = 42
) -> Dict[str, Any]:
    """Train character-level model using exact same split indices as Experiment 01."""
    output_dir.mkdir(parents=True, exist_ok=True)

    texts, labels, records = load_ml_data(dataset_path)

    # Recreate the exact stratified split
    indices = np.arange(len(texts))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=test_size,
        stratify=labels,
        random_state=random_state
    )

    # Verify split matches existing test_split.json if present
    saved_test_split_path = output_dir / "test_split.json"
    if saved_test_split_path.exists():
        with open(saved_test_split_path, "r", encoding="utf-8") as f:
            saved_split = json.load(f)
        saved_ids = [r["id"] for r in saved_split]
        current_test_ids = [records[i]["id"] for i in test_idx]
        if set(saved_ids) != set(current_test_ids):
            raise ValueError(
                f"Split indices mismatch with saved test_split.json!\n"
                f"Expected {len(saved_ids)} IDs, got {len(current_test_ids)}."
            )
        print("[OK] Verified: Exact train/test indices match Experiment 01.")

    X_train, y_train = texts[train_idx], labels[train_idx]
    X_test, y_test = texts[test_idx], labels[test_idx]

    print("=" * 65)
    print("SCAMCHECK ML EXPERIMENT 02 (Char TF-IDF + Logistic Regression)")
    print("=" * 65)
    print(f"Total dataset size:        {len(texts)}")
    print(f"Training set size:         {len(X_train)} (Scam: {np.sum(y_train == 'scam')}, Legitimate: {np.sum(y_train == 'legitimate')})")
    print(f"Test set size:             {len(X_test)} (Scam: {np.sum(y_test == 'scam')}, Legitimate: {np.sum(y_test == 'legitimate')})")
    print(f"Random Seed:               {random_state}")
    print(f"N-Gram Specification:      char_wb (3, 5), max_features=5000")
    print("-" * 65)

    # Fit pipeline strictly on X_train (zero leakage)
    pipeline = build_char_pipeline(random_state=random_state)
    pipeline.fit(X_train, y_train)

    train_acc = pipeline.score(X_train, y_train)
    test_acc = pipeline.score(X_test, y_test)

    print(f"Train Accuracy:            {train_acc:.4f}")
    print(f"Held-Out Test Accuracy:    {test_acc:.4f}")
    print("-" * 65)

    # Save Experiment 02 artifact
    model_file = output_dir / "scamcheck_char_lr_pipeline.joblib"
    joblib.dump(pipeline, model_file)
    print(f"Serialized model pipeline saved to: {model_file}")

    # Save training metadata
    meta = {
        "experiment_id": "EXP-02-CHAR-TFIDF-LOGREG",
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
            "model_type": "Character TF-IDF + LogisticRegression",
            "analyzer": "char_wb",
            "ngram_range": [3, 5],
            "max_features": 5000,
            "sublinear_tf": True,
            "C": 1.0,
            "class_weight": "balanced",
            "solver": "lbfgs"
        }
    }

    meta_file = output_dir / "training_meta_char.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Training metadata saved to:        {meta_file}")
    print("=" * 65)

    return meta


def main():
    parser = argparse.ArgumentParser(description="Train ScamCheck Experiment 02: Character TF-IDF Model")
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(backend_dir / "data" / "ml" / "dataset.json"),
        help="Path to ML dataset JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(backend_dir / "ml" / "models"),
        help="Directory to save model artifacts"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    train_char_model(
        dataset_path=Path(args.data_path),
        output_dir=Path(args.output_dir),
        random_state=args.seed
    )


if __name__ == "__main__":
    main()
