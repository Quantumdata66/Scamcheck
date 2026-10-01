# ScamCheck Machine Learning Experiment Pipeline

**Component:** ML Baseline Classifier & Experiment Scaffold  
**Location:** [`backend/ml/`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/)  
**Model Architecture:** Sublinear TF-IDF (1–2 n-grams) + Balanced L2 Logistic Regression  
**Status:** Scaffolding & Training Pipeline Ready

---

## 1. Overview & Architectural Purpose

The ScamCheck ML experiment framework establishes an explainable, lightweight natural language processing baseline for binary scam detection (`scam` vs. `legitimate`). 

It provides an empirical comparator against the deterministic rules baseline ([`RulesBaselineDetector`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/app/services/detector.py)), specifically designed to evaluate whether statistical n-gram representations can generalize across paraphrasing and syntactic perturbations where exact regex patterns break.

```
Raw Text Message
       │
       ▼
[ ml.preprocessing.clean_text ] ──> (Tokenizes URLs, phones, emails, crypto addrs, currency)
       │
       ▼
[ sklearn.feature_extraction.text.TfidfVectorizer ] ──> (Unigrams + Bigrams, Sublinear TF, 2500 max features)
       │
       ▼
[ sklearn.linear_model.LogisticRegression ] ──> (L2 Penalty, Balanced Class Weight, L-BFGS)
       │
       ▼
Binary Prediction: 'scam' | 'legitimate' + Probability Score P(scam)
```

---

## 2. Directory Structure

```
backend/ml/
├── preprocessing.py       # Entity normalization & text cleaning routines
├── train.py               # Reproducible training pipeline with zero data leakage
├── evaluate.py            # Comprehensive evaluation runner (test split & external benchmark)
├── README.md              # This documentation
└── models/                # Generated artifacts (created upon training)
    ├── scamcheck_lr_pipeline.joblib   # Serialized end-to-end sklearn Pipeline
    ├── test_split.json                 # Held-out test split for reproducibility
    ├── training_meta.json              # Training metadata, hyperparameters, and metrics
    └── evaluation_report.json          # Detailed classification metrics & confusion matrix
```

---

## 3. Data Hygiene & Leakage Prevention Protocol

1. **Strict Stratified Split:** The dataset ([`backend/data/ml/dataset.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/ml/dataset.json), $N=210$) is split 80/20 with `random_state=42` and stratification on the target label (`scam` / `legitimate`).
2. **Zero Train/Test Contamination:** Text cleaning and TF-IDF vocabulary extraction are fit **strictly** on the training partition ($N=168$) using a unified `sklearn.pipeline.Pipeline`. The held-out test partition ($N=42$) is never seen during vocabulary construction or feature scaling.
3. **External Benchmark Fixture Isolation:** The 37-example evaluation benchmark ([`backend/data/evaluation_fixture.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/evaluation_fixture.json)) remains 100% separate from training data and is used only as an independent out-of-distribution stress test during evaluation.

---

## 4. How to Run

### Step 1: Validate Dataset Integrity
```bash
python backend/data/ml/validate_dataset.py
```

### Step 2: Train the ML Pipeline
```bash
python backend/ml/train.py --data-path backend/data/ml/dataset.json --seed 42
```

### Step 3: Run Evaluation
```bash
python backend/ml/evaluate.py --model-path backend/ml/models/scamcheck_lr_pipeline.joblib
```

---

## 5. Hyperparameter Specification

- **Feature Extractor:** `TfidfVectorizer`
  - `ngram_range`: `(1, 2)` (captures single words and key phrase pairs like `"wire transfer"`, `"guaranteed returns"`)
  - `max_features`: `2500`
  - `sublinear_tf`: `True` (applies logarithmic sublinear scaling $1 + \log(\text{tf})$ to prevent high-frequency term dominance)
  - `strip_accents`: `'unicode'`
- **Classifier:** `LogisticRegression`
  - `C`: `1.0`
  - `penalty`: `'l2'`
  - `class_weight`: `'balanced'`
  - `solver`: `'lbfgs'`
  - `max_iter`: `1000`
  - `random_state`: `42`
