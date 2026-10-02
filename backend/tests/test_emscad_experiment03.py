"""
Unit tests for ScamCheck ML Experiment 03 (EMSCAD-Trained Fake-Job Classifier).

Validates:
1. Split manifest integrity, proportions, and zero-leakage disjointness.
2. Model artifact loading and expected pipeline steps.
3. Prediction serialization schema and label consistency.
4. Short-message diagnostic transfer mapping correctness.
"""

import json
from pathlib import Path
import pytest
import joblib
import numpy as np

backend_dir = Path(__file__).resolve().parent.parent
MODELS_DIR = backend_dir / "ml" / "models"
RESULTS_DIR = backend_dir / "ml" / "results" / "emscad"


class TestExperiment03SplitIntegrity:
    """Validate that EMSCAD train/val/test splits satisfy strict partitioning and isolation."""

    @pytest.fixture(scope="module")
    def split_manifest(self):
        manifest_path = MODELS_DIR / "emscad_splits.json"
        assert manifest_path.exists(), f"Missing split manifest at: {manifest_path}"
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_split_proportions(self, split_manifest):
        counts = split_manifest["counts"]
        total = split_manifest["total_unique_records"]
        assert total == 16201, f"Expected 16,201 unique records, got {total}"

        train_count = counts["train"]["total"]
        val_count = counts["validation"]["total"]
        test_count = counts["test"]["total"]

        assert train_count + val_count + test_count == total
        assert abs(train_count / total - 0.70) < 0.01, f"Train proportion {train_count / total} not ~70%"
        assert abs(val_count / total - 0.15) < 0.01, f"Val proportion {val_count / total} not ~15%"
        assert abs(test_count / total - 0.15) < 0.01, f"Test proportion {test_count / total} not ~15%"

    def test_partition_disjointness(self, split_manifest):
        train_ids = set(split_manifest["train_job_ids"])
        val_ids = set(split_manifest["validation_job_ids"])
        test_ids = set(split_manifest["test_job_ids"])

        assert train_ids.isdisjoint(val_ids), "Train and Validation partitions share job IDs!"
        assert train_ids.isdisjoint(test_ids), "Train and Test partitions share job IDs!"
        assert val_ids.isdisjoint(test_ids), "Validation and Test partitions share job IDs!"


class TestExperiment03ModelArtifact:
    """Verify Experiment 03 trained pipeline structure and serialization."""

    @pytest.fixture(scope="module")
    def model_pipeline(self):
        model_path = MODELS_DIR / "scamcheck_emscad_fake_job_pipeline.joblib"
        assert model_path.exists(), f"Missing Experiment 03 model at: {model_path}"
        return joblib.load(model_path)

    def test_pipeline_steps(self, model_pipeline):
        step_names = list(model_pipeline.named_steps.keys())
        assert step_names == ["preprocessor", "tfidf", "classifier"]

    def test_classes(self, model_pipeline):
        classes = list(model_pipeline.classes_)
        assert "legitimate" in classes
        assert "scam" in classes

    def test_inference_shape(self, model_pipeline):
        sample_texts = [
            "Job Title: Software Engineer\n\nDescription: Developing full-stack web applications.",
            "Job Title: Urgent Cashier Needed\n\nDescription: Wire $100 upfront for background checks."
        ]
        preds = model_pipeline.predict(sample_texts)
        probas = model_pipeline.predict_proba(sample_texts)

        assert len(preds) == 2
        assert probas.shape == (2, 2)
        assert np.allclose(probas.sum(axis=1), 1.0)


class TestExperiment03MetadataAndMetrics:
    """Verify Experiment 03 metadata, test predictions, and validation results."""

    def test_training_metadata_exists_and_valid(self):
        meta_path = MODELS_DIR / "training_meta_emscad.json"
        assert meta_path.exists()

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert meta["experiment_id"] == "EXP-03-EMSCAD-FAKE-JOB"
        assert "test_metrics" in meta
        assert meta["test_metrics"]["accuracy"] > 0.90
        assert meta["test_metrics"]["scam_f1"] > 0.60
        assert "short_message_benchmark_transfer" in meta

    def test_test_predictions_count_matches(self):
        pred_path = MODELS_DIR / "emscad_test_predictions.json"
        assert pred_path.exists()

        with open(pred_path, "r", encoding="utf-8") as f:
            preds = json.load(f)

        assert len(preds) == 2431, f"Expected 2,431 test predictions, got {len(preds)}"
        for p in preds:
            assert p["true_label"] in ("legitimate", "scam")
            assert p["predicted_label"] in ("legitimate", "scam")
            assert 0.0 <= p["p_scam"] <= 1.0

    def test_benchmark_predictions_count_matches(self):
        pred_path = MODELS_DIR / "benchmark_predictions_emscad.json"
        assert pred_path.exists()

        with open(pred_path, "r", encoding="utf-8") as f:
            preds = json.load(f)

        assert len(preds) == 37, f"Expected 37 benchmark predictions, got {len(preds)}"
