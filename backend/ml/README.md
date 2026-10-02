# ScamCheck Machine Learning Experiment Pipeline

**Component:** ML Models, Dataset Foundations & Evaluation Suite  
**Location:** [`backend/ml/`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/)  
**Status:** Experiments 01, 02, and 03 Completed  

---

## 1. Overview & Architectural Purpose

The ScamCheck ML experiment framework provides empirical natural language processing models for binary scam detection (`scam` vs. `legitimate`).

It compares statistical n-gram representations against the deterministic rules baseline ([`RulesBaselineDetector`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/app/services/detector.py)), evaluating robustness across syntactic perturbations, character obfuscation, and cross-modality domain transfers.

```
┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐
│  Short Messages (SMS/WhatsApp/DMs)     │     │  Long Documents (Job Board Ads)        │
│  - 20–60 words                         │     │  - 350–900 words                       │
│  - Urgent imperatives & payment lures  │     │  - Boilerplate corporate ATS text      │
└───────────────────┬────────────────────┘     └───────────────────┬────────────────────┘
                    │                                              │
                    ▼                                              ▼
    [ EXP-01 & EXP-02 Models ]                     [ EXP-03 EMSCAD Model ]
    - Word TF-IDF (1–2) + LR                       - Word Unigram TF-IDF (1–1) + LR
    - Char TF-IDF (3–5) + LR                       - High in-domain precision (65.96%)
    - High adversarial robustness (61.5%)          - High in-domain recall (86.11%)
```

---

## 2. Directory Structure & Experiment Artifacts

```
backend/ml/
├── preprocessing.py                    # Entity normalization & text cleaning routines
├── train.py                            # Experiment 01 training script (Word TF-IDF)
├── train_char.py                       # Experiment 02 training script (Character TF-IDF)
├── train_emscad.py                     # Experiment 03 training script (EMSCAD fake-job model)
├── evaluate.py                         # Evaluation runner for short-message models
├── evaluate_emscad.py                  # Zero-shot out-of-domain evaluation runner for EMSCAD
├── ML_EXPERIMENT_01.md                 # Experiment 01 full report
├── ML_EXPERIMENT_02.md                 # Experiment 02 full report
├── ML_EXPERIMENT_03.md                 # Experiment 03 full report
├── EMSCAD_DATA_PROFILE.md              # EMSCAD structural data audit
├── EMSCAD_EXTERNAL_EVALUATION.md       # Zero-shot EMSCAD evaluation report
├── README.md                           # This documentation
├── models/                             # Serialized pipelines, metadata, & prediction logs
│   ├── scamcheck_lr_pipeline.joblib                # Exp 01 Word TF-IDF model
│   ├── scamcheck_char_lr_pipeline.joblib           # Exp 02 Char TF-IDF model
│   ├── scamcheck_emscad_fake_job_pipeline.joblib   # Exp 03 EMSCAD fake-job model
│   ├── test_split.json                             # 42-sample synthetic test split manifest
│   ├── emscad_splits.json                          # 16,201-sample EMSCAD 70/15/15 split manifest
│   ├── training_meta.json                          # Exp 01 metadata
│   ├── training_meta_char.json                     # Exp 02 metadata
│   ├── training_meta_emscad.json                   # Exp 03 metadata
│   ├── test_predictions.json                       # Exp 01 test predictions
│   ├── test_predictions_char.json                  # Exp 02 test predictions
│   ├── emscad_test_predictions.json                # Exp 03 test predictions
│   ├── benchmark_predictions.json                  # Exp 01 benchmark predictions
│   ├── benchmark_predictions_char.json             # Exp 02 benchmark predictions
│   └── benchmark_predictions_emscad.json           # Exp 03 benchmark transfer predictions
└── results/
    └── emscad/
        ├── emscad_evaluation_summary.json          # Zero-shot evaluation metrics (Exp 01 & 02)
        └── emscad_validation_metrics.json          # Validation tuning grid metrics (Exp 03)
```

---

## 3. Experiment Summary & Performance Matrix

| Metric / Partition | Rules Baseline | EXP-01: Word TF-IDF | EXP-02: Char TF-IDF | EXP-03: EMSCAD Model |
| :--- | :--- | :--- | :--- | :--- |
| **Training Source** | Handcrafted Regex | Synthetic Short ($N=168$) | Synthetic Short ($N=168$) | EMSCAD Long ($N=11,340$) |
| **Feature Analyzer** | Rule Matching | Word (1–2), Max 2.5k | Char-WB (3–5), Max 5k | Word (1–1), Max 10k |
| **Held-Out Test Accuracy** | N/A | **97.62%** ($N=42$) | 90.48% ($N=42$) | **97.41%** ($N=2,431$) |
| **Held-Out Scam Recall** | N/A | **95.24%** (20/21) | 85.71% (18/21) | **86.11%** (93/108) |
| **Held-Out Scam-F1** | N/A | **0.9756** | 0.9000 | **0.7470** |
| **Held-Out Scam PR-AUC** | N/A | N/A (Balanced) | N/A (Balanced) | **0.8616** |
| **Short Benchmark Accuracy ($N=37$)** | 59.46% (3-tier) | **81.08%** | **81.08%** | **51.35%** (Out-of-domain) |
| **Adversarial Subset ($N=13$)** | 0.00% (0/13) | 53.85% (7/13) | **61.54%** (8/13) | 23.08% (3/13) |
| **EMSCAD Zero-Shot Accuracy ($N=16,201$)** | N/A | 92.52% | 95.09% | **97.41%** (In-domain test) |
| **EMSCAD Scam Precision** | N/A | 15.47% | 34.69% | **65.96%** |
| **EMSCAD Scam Recall** | N/A | 15.26% | 11.79% | **86.11%** |

---

## 4. How to Reproduce All Experiments

```bash
# Step 1: Validate synthetic dataset
python backend/data/ml/validate_dataset.py

# Step 2: Train Experiment 01 (Word TF-IDF)
python backend/ml/train.py --seed 42

# Step 3: Train Experiment 02 (Char TF-IDF)
python backend/ml/train_char.py

# Step 4: Train Experiment 03 (EMSCAD Fake-Job Classifier)
python backend/ml/train_emscad.py --seed 42

# Step 5: Run EMSCAD Zero-Shot Evaluation (Evaluates Exp 01 & 02)
python backend/ml/evaluate_emscad.py

# Step 6: Run Full Backend Test Suite
pytest backend/tests
```

---

## 5. Architectural Conclusions & Key Takeaways

1. **Short Message Domain (SMS/WhatsApp):**  
   Word and Character TF-IDF models (Exp 01 & 02) excel at short-message classification and boost adversarial resilience from 0% to 61.54%.
2. **Long Document Domain (Job Board ATS Ads):**  
   The EMSCAD model (Exp 03) provides deep fake-job detection for full job descriptions (86.11% recall, 0.8616 PR-AUC).
3. **Cross-Modality Transfer Limitation:**  
   Models trained on long vacancy postings experience severe modality collapse when transferred to short SMS messages (dropping to 30.43% scam recall). Therefore, ScamCheck should use message-length routing rather than attempting a single universal model.
