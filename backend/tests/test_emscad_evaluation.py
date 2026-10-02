"""
Focused tests for EMSCAD external evaluation pipeline.

Validates:
1. Safe text composition (skipping nulls, string 'nan'/'none', empty fields).
2. Binary label mapping and error handling.
3. Normalized text deduplication.
4. Metric computations and majority-class baseline.
5. Benchmark isolation checks.
"""

import pytest
import numpy as np
from ml.evaluate_emscad import (
    compose_emscad_text,
    map_emscad_label,
    deduplicate_records,
    compute_metrics,
    compute_majority_baseline
)


class TestEMSCADTextComposition:
    """Test safe composition of multi-field job postings."""

    def test_complete_row_composition(self):
        row = {
            "title": "Senior React Developer",
            "company_profile": "Acme Corp is a fintech innovator.",
            "description": "Build high-scale user interfaces in React 19.",
            "requirements": "5+ years of TypeScript experience.",
            "benefits": "Competitive salary, 401(k) matching, remote work."
        }
        text = compose_emscad_text(row)
        assert "Job Title: Senior React Developer" in text
        assert "Company Profile: Acme Corp is a fintech innovator." in text
        assert "Description: Build high-scale user interfaces in React 19." in text
        assert "Requirements: 5+ years of TypeScript experience." in text
        assert "Benefits: Competitive salary, 401(k) matching, remote work." in text

    def test_missing_and_nan_fields_filtered(self):
        row = {
            "title": "Customer Service Rep",
            "company_profile": "nan",
            "description": "Answer inbound customer inquiries.",
            "requirements": None,
            "benefits": "  None  "
        }
        text = compose_emscad_text(row)
        assert "Job Title: Customer Service Rep" in text
        assert "Description: Answer inbound customer inquiries." in text
        assert "Company Profile" not in text
        assert "Requirements" not in text
        assert "Benefits" not in text

    def test_all_empty_fields_returns_empty_string(self):
        row = {
            "title": "  ",
            "company_profile": "nan",
            "description": None,
            "requirements": "null",
            "benefits": "N/A"
        }
        text = compose_emscad_text(row)
        assert text == ""


class TestEMSCADLabelMapping:
    """Test conversion of fraudulent indicators to ScamCheck binary contract."""

    @pytest.mark.parametrize("input_val,expected", [
        (1, "scam"),
        ("1", "scam"),
        (1.0, "scam"),
        ("1.0", "scam"),
        ("true", "scam"),
        ("True", "scam"),
        ("t", "scam"),
        ("T", "scam"),
        (0, "legitimate"),
        ("0", "legitimate"),
        (0.0, "legitimate"),
        ("0.0", "legitimate"),
        ("false", "legitimate"),
        ("False", "legitimate"),
        ("f", "legitimate"),
        ("F", "legitimate"),
    ])
    def test_valid_label_mappings(self, input_val, expected):
        assert map_emscad_label(input_val) == expected

    @pytest.mark.parametrize("invalid_val", [
        None,
        "unknown",
        "-1",
        "2",
        "fraud",
        "",
        " "
    ])
    def test_invalid_label_raises_value_error(self, invalid_val):
        with pytest.raises(ValueError):
            map_emscad_label(invalid_val)


class TestEMSCADDeduplication:
    """Test deduplication of normalized texts and conflict auditing."""

    def test_deduplication_removes_whitespace_case_duplicates(self):
        records = [
            {"job_id": "1", "text": "Hiring React Dev. Apply now.", "label": "legitimate"},
            {"job_id": "2", "text": "  HIRING   REACT DEV.   APPLY NOW.  ", "label": "legitimate"},
            {"job_id": "3", "text": "Hiring Python Engineer.", "label": "legitimate"},
        ]
        unique_records, audit = deduplicate_records(records)
        assert len(unique_records) == 2
        assert audit["duplicate_instances_same_label"] == 1
        assert audit["conflicting_label_groups"] == 0
        assert unique_records[0]["job_id"] == "1"
        assert unique_records[1]["job_id"] == "3"

    def test_deduplication_detects_and_excludes_conflicting_labels(self):
        records = [
            {"job_id": "1", "text": "Urgent customer support role.", "label": "legitimate"},
            {"job_id": "2", "text": "urgent customer support role.", "label": "scam"},
            {"job_id": "3", "text": "Verified corporate role.", "label": "legitimate"},
        ]
        unique_records, audit = deduplicate_records(records)
        # Conflicting group with 2 records is excluded
        assert len(unique_records) == 1
        assert audit["conflicting_label_groups"] == 1
        assert unique_records[0]["job_id"] == "3"


class TestEMSCADMetrics:
    """Test evaluation metrics and majority class baseline calculation."""

    def test_metrics_calculation(self):
        y_true = ["legitimate", "legitimate", "legitimate", "scam"]
        y_pred = ["legitimate", "legitimate", "scam", "scam"]
        probas = np.array([0.1, 0.2, 0.8, 0.9])

        metrics = compute_metrics(y_true, y_pred, probas)
        assert metrics["accuracy"] == 0.75
        assert metrics["confusion_matrix"]["true_legitimate_pred_legitimate_tn"] == 2
        assert metrics["confusion_matrix"]["true_legitimate_pred_scam_fp"] == 1
        assert metrics["confusion_matrix"]["true_scam_pred_legitimate_fn"] == 0
        assert metrics["confusion_matrix"]["true_scam_pred_scam_tp"] == 1
        assert metrics["scam_metrics"]["recall"] == 1.0
        assert metrics["scam_metrics"]["precision"] == 0.5
        assert metrics["pr_auc"] is not None

    def test_majority_baseline_predicts_all_legitimate(self):
        y_true = ["legitimate"] * 95 + ["scam"] * 5
        base_metrics = compute_majority_baseline(y_true)

        assert base_metrics["accuracy"] == 0.95
        assert base_metrics["scam_metrics"]["precision"] == 0.0
        assert base_metrics["scam_metrics"]["recall"] == 0.0
        assert base_metrics["scam_metrics"]["f1"] == 0.0
        assert base_metrics["confusion_matrix"]["true_scam_pred_scam_tp"] == 0
        assert base_metrics["confusion_matrix"]["true_scam_pred_legitimate_fn"] == 5
