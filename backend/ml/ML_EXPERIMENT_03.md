# ScamCheck ML Experiment 03: EMSCAD-Trained Fake-Job Classifier & Cross-Modality Transfer

**Experiment ID:** `EXP-03-EMSCAD-FAKE-JOB`  
**Date:** October 2026  
**Status:** Completed  
**Training Script:** [`backend/ml/train_emscad.py`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/train_emscad.py)  
**Model Pipeline Artifact:** [`backend/ml/models/scamcheck_emscad_fake_job_pipeline.joblib`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/scamcheck_emscad_fake_job_pipeline.joblib)  
**Split Manifest:** [`backend/ml/models/emscad_splits.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/emscad_splits.json)  
**Validation Grid Metrics:** [`backend/ml/results/emscad/emscad_validation_metrics.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/results/emscad/emscad_validation_metrics.json)  
**Training Metadata:** [`backend/ml/models/training_meta_emscad.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/training_meta_emscad.json)  
**Prediction Logs:**  
- Test Split Predictions ($N=2,431$): [`backend/ml/models/emscad_test_predictions.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/emscad_test_predictions.json)  
- Short-Message Diagnostic Transfer ($N=37$): [`backend/ml/models/benchmark_predictions_emscad.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/benchmark_predictions_emscad.json)  

---

## 1. Executive Summary & Experiment Objectives

Experiments 01 and 02 trained models on ScamCheck's curated short-message dataset ($N=210$) and evaluated zero-shot transfer onto EMSCAD ($N=16,201$). 

**Experiment 03 reverses this relationship:**
1. Train a native binary classifier directly on the **EMSCAD employment scam dataset** to establish an upper bound for in-domain fake-job classification on long-form vacancy announcements.
2. Evaluate **zero-shot cross-modality transfer** by testing the frozen EMSCAD model on ScamCheck's 37-example short-message benchmark fixture ([`evaluation_fixture.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/evaluation_fixture.json)).
3. Test the core architectural hypothesis: *Can a model trained on formal long-form recruitment ads transfer effectively to short inbound SMS/WhatsApp/Telegram conversational smishing?*

---

## 2. Dataset Preparation, Deduplication & Leakage Prevention

- **Raw Source:** [`backend/data/external/emscad/fake_job_postings.csv`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/external/emscad/fake_job_postings.csv) ($17,880$ raw rows)
- **Text Composition:** Non-null concatenation of `title`, `company_profile`, `description`, `requirements`, and `benefits` (filtering string null tokens `'nan'`, `'none'`, `'null'`, `'n/a'`).
- **Deduplication Audit:**
  - $16,201$ unique records identified after whitespace and case normalization.
  - $1,679$ duplicate instances removed.
  - **$0$ conflicting label groups** (100% ground-truth label consistency across duplicates).
- **Stratified Partitioning (70% Train / 15% Validation / 15% Test):**
  - Random Seed: `42` (Fixed and deterministic).
  - Exact split manifests, counts, and job IDs saved in [`emscad_splits.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/emscad_splits.json).
- **Zero-Contamination Safeguards:**
  - `TextCleaner` and `TfidfVectorizer` vocabulary fitting occurred **strictly on the Training partition ($N=11,340$)**.
  - Validation and Test partitions were transformed with zero refitting.
  - The 210 synthetic training samples and the 37-example evaluation benchmark were **never included** in EMSCAD training.

### Partition Distribution:
| Partition | Total Unique Records | Scam Records (`t`) | Legitimate Records (`f`) | Class Imbalance Ratio |
| :--- | :--- | :--- | :--- | :--- |
| **Training Partition (70%)** | 11,340 | 505 (4.45%) | 10,835 (95.55%) | 21.5 : 1 |
| **Validation Partition (15%)** | 2,430 | 108 (4.44%) | 2,322 (95.56%) | 21.5 : 1 |
| **Held-Out Test Partition (15%)**| 2,431 | 108 (4.44%) | 2,323 (95.56%) | 21.5 : 1 |
| **TOTAL EVALUATED** | **16,201** | **721 (4.45%)** | **15,480 (95.55%)** | **21.5 : 1** |

---

## 3. Validation Model Selection & Hyperparameter Tuning

A focused grid of 5 candidate configurations was trained on the Training Partition ($N=11,340$) and evaluated on the held-out Validation Partition ($N=2,430$):

| Candidate ID | Model & Hyperparameter Configuration | Val Macro-F1 | Val Scam Precision | Val Scam Recall | Val Scam F1 | Val PR-AUC | Selection Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CONFIG_01` | Word TF-IDF (1-2), Max 10k, $C=1.0$, balanced | 0.8330 | 0.5759 | 0.8426 | 0.6842 | 0.8257 | 1.6586 |
| `CONFIG_02` | Word TF-IDF (1-2), Max 10k, $C=0.5$, balanced | 0.8169 | 0.5353 | 0.8426 | 0.6547 | 0.8061 | 1.6230 |
| `CONFIG_03` | Word TF-IDF (1-2), Max 10k, $C=2.0$, balanced | 0.8528 | 0.6403 | 0.8241 | 0.7206 | 0.8431 | 1.6960 |
| **`CONFIG_04` (WINNER)**| **Word TF-IDF (1-1) Unigram, Max 10k, $C=1.0$, balanced** | **0.8522** | **0.6144** | **0.8704** | **0.7203** | **0.8441** | **1.6963** |
| `CONFIG_05` | Char-WB TF-IDF (3-4), Max 5k, $C=1.0$, balanced | 0.8130 | 0.5227 | 0.8519 | 0.6479 | 0.8028 | 1.6158 |

### Selection Rationale & Metric Definitions:
- **Winning Configuration (`CONFIG_04`):** Word Unigram TF-IDF (`ngram_range=(1, 1)`, `max_features=10,000`, `sublinear_tf=True`, `min_df=2`, `C=1.0`, `class_weight='balanced'`).
- **Validation Selection Score:** Calculated as a custom composite heuristic:
  $$\text{Selection Score} = \text{Validation Macro-F1} + \text{Validation Scam PR-AUC}$$
  *(Note: This is an internal decision criterion combining overall balanced accuracy with threshold-independent precision-recall curve ranking on the validation partition, rather than a standalone standard metric).*
- **Performance:** Achieved the highest validation composite score ($1.6963$) with **87.04% scam recall** and **0.8441 PR-AUC**.
- Unigrams outperformed bigrams and character n-grams on EMSCAD because long job descriptions contain high keyword repetition where single discriminatory tokens (`wire`, `commission`, `unlimited`, `reimbursement`) provide clearer separation than noisy bigrams.

---

## 4. Final Evaluation: Held-Out EMSCAD Test Partition ($N=2,431$)

The winning pipeline was evaluated **exactly once** on the held-out test partition:

### Summary Performance vs. Majority Baseline:
| Metric | Majority Baseline (Predict All Legit) | EXP-03 EMSCAD Classifier | Delta vs Baseline |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 95.56% | **97.41%** (2,368 / 2,431) | **+1.85%** |
| **Macro F1-Score** | 0.4886 | **0.8667** | **+0.3781** |
| **Macro Precision** | 0.4778 | **0.8265** | **+0.3487** |
| **Macro Recall** | 0.5000 | **0.9202** | **+0.4202** |
| **Scam Precision** | 0.00% | **65.96%** (93 / 141) | **+65.96%** |
| **Scam Recall (Sensitivity)** | 0.00% | **86.11%** (93 / 108) | **+86.11%** |
| **Scam F1-Score** | 0.00% | **0.7470** | **+0.7470** |
| **Scam PR-AUC** | 0.0444 (Base rate) | **0.8616** | **+0.8172 (19.4x baseline)** |
| **Legitimate Precision** | 95.56% | **99.34%** (2,275 / 2,290) | +3.78% |
| **Legitimate Recall** | 100.00% | **97.93%** (2,275 / 2,323) | -2.07% |
| **Legitimate F1-Score** | 0.9773 | **0.9863** | +0.90% |

### Confusion Matrix (Held-Out Test Partition):
```text
                                Predicted Legitimate    Predicted Scam
Actual Legitimate (2,323)              2,275                 48   (False Positives = 2.07%)
Actual Scam (108)                         15                 93   (True Positives = 86.11%)
```

---

## 5. Diagnostic Error Analysis (Test Partition)

### A. False Positives ($N=48$, 2.07% of legitimate ads)
1. **High-Turnover / Commission Sales Roles:** Roles advertising rapid recruitment, high sales bonuses, or independent contractor status (e.g. `emscad_8871` *"Business Account Manager... If you're a closer..."*, $P_{\text{scam}}=0.767$; `emscad_3026` *"Sales Executive"*, $P_{\text{scam}}=0.609$).
2. **Consulting & Remote Agency Postings:** Small overseas staffing agencies without rich corporate history (e.g. `emscad_16780` *"QMS Consultant Required for UAE"*, $P_{\text{scam}}=0.680$).

### B. False Negatives ($N=15$, 13.89% of fraudulent ads)
1. **Professional ATS Description Clones:** Sophisticated scammers who cloned authentic job postings from major corporations verbatim (e.g. `emscad_5073` *"San Jose Water Company Founded in 1866..."*, $P_{\text{scam}}=0.488$; `emscad_17644` *"Fidelity"*, $P_{\text{scam}}=0.425$). The textual vocabulary was completely legitimate; the fraudulent signal resided entirely in the spoofed contact metadata.
2. **Extremely Short Minimalist Postings:** Postings with minimal text (e.g. `emscad_14270` *"Job Title: Northwestern Hospital... Description: build a website"*, $P_{\text{scam}}=0.301$).

---

## 6. Diagnostic Short-Message Transfer Evaluation ([`evaluation_fixture.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/evaluation_fixture.json), $N=37$)

To test cross-modality generalization, the frozen Experiment 03 pipeline was evaluated on ScamCheck's short-message benchmark fixture using the documented binary mapping (`high`/`needs_verification` $\rightarrow$ `scam`, `low` $\rightarrow$ `legitimate`):

> [!WARNING]
> This evaluation is an out-of-domain cross-modality diagnostic. It is NOT a representative estimate of performance on full-length vacancy notices.

### Transfer Benchmark Metrics:
- **Overall Benchmark Accuracy:** **51.35%** (19 / 37) [Exp 01: 81.08%, Exp 02: 81.08%]
- **Macro F1-Score:** **0.5045** [Exp 01: 0.8015, Exp 02: 0.8015]
- **Scam Precision:** **77.78%** (7 / 9)
- **Scam Recall:** **30.43%** (7 / 23) [Exp 01: 82.61%, Exp 02: 82.61%]
- **Scam F1-Score:** **0.4375** [Exp 01: 0.8444, Exp 02: 0.8444]
- **Standard & Benign Subset Accuracy ($N=24$):** **66.67%** (16 / 24)
- **Adversarial Subset Accuracy ($N=13$):** **23.08%** (3 / 13)

### Why Short-Message Transfer Collapsed (30.43% Recall):
1. **Domain & Threat Vector Mismatch:**  
   The EMSCAD model was trained exclusively on recruitment fraud in long vacancy postings. When presented with bank smishing (`SCAM_BANK_001` *"Your account has been suspended..."*) or crypto investment scams (`SCAM_INV_001` *"Double your Bitcoin..."*), the model has zero prior exposure to banking suspension tokens or crypto liquidity terminology.
2. **Text Length & Prior Distribution:**  
   EMSCAD postings average 450 words. In 30-word SMS messages, the unigram feature density is sparse, causing the classifier's prior to default toward legitimate predictions ($P_{\text{scam}} < 0.40$).

---

## 7. Global Cross-Experiment Comparison Matrix

| Evaluation Dimension | Rules Baseline Detector | EXP-01: Word TF-IDF (Synthetic) | EXP-02: Char TF-IDF (Synthetic) | EXP-03: EMSCAD Fake-Job Classifier |
| :--- | :--- | :--- | :--- | :--- |
| **Training Data Source** | Expert Heuristics / Regex | 210 Synthetic Short Messages | 210 Synthetic Short Messages | 11,340 EMSCAD Long Postings |
| **Target Scope** | Multi-Domain (Bank/Job/Inv) | Multi-Domain (Bank/Job/Inv) | Multi-Domain (Bank/Job/Inv) | Fake-Job Vacancy Specific |
| **In-Domain Test Accuracy** | 90.9% (Curated subset) | **97.62%** ($N=42$) | 90.48% ($N=42$) | **97.41%** ($N=2,431$) |
| **In-Domain Scam-F1** | N/A | **0.9756** | 0.9000 | **0.7470** |
| **In-Domain Scam PR-AUC** | N/A | N/A (Balanced test) | N/A (Balanced test) | **0.8616** (Imbalanced 21.5:1) |
| **Short-Message Benchmark ($N=37$)**| 59.46% (3-tier) | **81.08%** | **81.08%** | **51.35%** (Out-of-domain) |
| **Adversarial Subset ($N=13$)** | 0.00% (0/13) | 53.85% (7/13) | **61.54%** (8/13) | 23.08% (3/13) |
| **EMSCAD Zero-Shot Precision** | N/A | 15.47% | 34.69% | **65.96%** (In-domain) |
| **EMSCAD Zero-Shot Recall** | N/A | 15.26% | 11.79% | **86.11%** (In-domain) |

---

## 8. Strategic Conclusions & Architectural Recommendations

1. **EMSCAD is a High-Quality Domain-Specific Expert, Not a General Smishing Detector:**  
   Experiment 03 confirms that EMSCAD produces an exceptional classifier for long-form job boards (**86.11% recall, 65.96% precision, 0.8616 PR-AUC**), but is unsuited as a standalone detector for short SMS smishing due to severe modality collapse (30.43% transfer recall).
2. **Recommended Multi-Tier Architecture:**  
   ScamCheck should adopt an **ensemble / routing architecture**:
   - **Short Messages (< 100 words):** Routed to the Experiment 01/02 ensemble (Word + Char TF-IDF) combined with rules-based explainability.
   - **Long Documents / Job Descriptions (> 100 words):** Routed to the Experiment 03 EMSCAD expert classifier for deep recruitment fraud inspection.
