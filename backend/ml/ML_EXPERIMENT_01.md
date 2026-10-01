# ScamCheck ML Experiment 01: Baseline TF-IDF + Logistic Regression Classifier

**Experiment ID:** `EXP-01-TFIDF-LOGREG`  
**Date:** October 2026  
**Status:** Completed  
**Pipeline Location:** [`backend/ml/`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/)  
**Model Artifact:** [`backend/ml/models/scamcheck_lr_pipeline.joblib`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/scamcheck_lr_pipeline.joblib)  
**Predictions Artifacts:**  
- Test Split Predictions: [`backend/ml/models/test_predictions.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/test_predictions.json)  
- Benchmark Predictions: [`backend/ml/models/benchmark_predictions.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/benchmark_predictions.json)  

---

## 1. Experiment Objective

The primary objective of Experiment 01 is to evaluate whether a lightweight statistical NLP model (TF-IDF + Logistic Regression) can:
1. Accurately separate `scam` vs. `legitimate` text across the three target domains (`bank_payment`, `fake_job`, `investment`, and general benign messages).
2. Generalize to paraphrased and obfuscated adversarial variations that broke the strict token matching of the rules-based detector.
3. Establish an initial machine learning baseline with zero data leakage and reproducible seeds for subsequent model iterations.

---

## 2. Dataset & Partitioning Protocol

- **Dataset Source:** [`backend/data/ml/dataset.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/ml/dataset.json) ($N=210$ total samples)
- **Validation Status:** PASSED (100% schema compliance, 0 duplicates, 0 overlap with benchmark fixture).
- **Split Strategy:** Stratified 80/20 train/test split.
- **Random Seed:** `42` (Fixed and reproducible).
- **Data Leakage Safeguards:**
  - Tokenization, entity normalization, and TF-IDF vocabulary extraction were fit **strictly on the training split** ($N=168$).
  - The held-out test split ($N=42$) was transformed without refitting.
  - The 37-example evaluation benchmark ([`backend/data/evaluation_fixture.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/evaluation_fixture.json)) remained completely untouched and isolated for external evaluation.

### Partition Sizes:
| Partition | Total Samples | Scam Samples | Legitimate Samples | Class Balance |
| :--- | :--- | :--- | :--- | :--- |
| **Training Set** | 168 | 84 | 84 | 50.0% / 50.0% |
| **Held-Out Test Set** | 42 | 21 | 21 | 50.0% / 50.0% |
| **TOTAL** | **210** | **105** | **105** | **50.0% / 50.0%** |

---

## 3. Model Configuration & Pipeline Hyperparameters

The end-to-end model is implemented as a scikit-learn `Pipeline`:

```text
Input Text ──> TextCleaner (Entity Normalization) ──> TfidfVectorizer ──> LogisticRegression
```

### Exact Hyperparameters:
- **Preprocessing:**
  - Entity masking: URLs $\rightarrow$ `__url__`, Phone numbers $\rightarrow$ `__phone__`, Emails $\rightarrow$ `__email__`, Crypto addresses $\rightarrow$ `__crypto_addr__`, Currency $\rightarrow$ `__currency__`.
  - Case folding: Lowercase conversion.
  - Whitespace & excessive punctuation normalization.
- **Feature Extractor (`TfidfVectorizer`):**
  - `ngram_range`: `(1, 2)` (Unigrams and Bigrams)
  - `max_features`: `2500`
  - `sublinear_tf`: `True` ($1 + \log(\text{tf})$)
  - `strip_accents`: `'unicode'`
  - `min_df`: `1`
  - Vocabulary Size: `1,678` extracted features.
- **Classifier (`LogisticRegression`):**
  - `C`: `1.0` (L2 Regularization)
  - `class_weight`: `'balanced'`
  - `solver`: `'lbfgs'`
  - `max_iter`: `1000`
  - `random_state`: `42`

---

## 4. Evaluation 1: Held-Out Synthetic Test Set ($N=42$)

### Summary Metrics:
- **Training Accuracy:** **100.0%** (168/168)
- **Held-Out Test Accuracy:** **97.62%** (41/42)
- **Macro Precision:** **0.9773**
- **Macro Recall:** **0.9762**
- **Macro F1-Score:** **0.9762**

### Per-Class Performance Table:
| Class | Support | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| **`legitimate`** | 21 | 0.9545 | 1.0000 | 0.9767 |
| **`scam`** | 21 | 1.0000 | 0.9524 | 0.9756 |
| **MACRO AVERAGE** | **42** | **0.9773** | **0.9762** | **0.9762** |

### Confusion Matrix (Held-Out Test Set):
```text
                  Predicted Legitimate    Predicted Scam
True Legitimate            21                   0   (False Positives = 0)
True Scam                   1                  20   (False Negatives = 1)
```

### Error Analysis (Held-Out Test Set):
- **False Positives (FP):** **0** (No legitimate message was misclassified as a scam).
- **False Negatives (FN):** **1**
  - **Sample ID:** `ML_SYNTH_005`
  - **True Label:** `scam` | **Predicted Label:** `legitimate` ($P_{\text{scam}} = 0.489$)
  - **Text:** *"URGENT NOTICE: Your debit card ending in 4108 has been temporarily restricted. Enter your PIN and card security code at https://secure-bank-reactivate.cc to restore access."*
  - **Diagnostic:** The predicted probability for scam was $0.489$, barely falling below the standard $0.50$ decision threshold. The combination of normalized tokens (`__url__`) and card service vocabulary without extreme scam unigrams caused a slight margin miss.

---

## 5. Evaluation 2: Isolated Benchmark Fixture ([`evaluation_fixture.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/evaluation_fixture.json), $N=37$)

### Risk-Tier to Binary Mapping Methodology:
The evaluation fixture was originally created for the 3-tier rules baseline (`low`, `needs_verification`, `high`). To enable a defensible binary comparison without modifying the benchmark:
- **`scam`:** Maps to `high` and `needs_verification` (any message warranting caution or intervention).
- **`legitimate`:** Maps to `low` (messages confirmed as benign, educational, or standard operations).

### Benchmark Metrics ($N=37$):
- **Overall Accuracy:** **81.08%** (30/37)
- **Macro Precision:** **0.7985**
- **Macro Recall:** **0.8059**
- **Macro F1-Score:** **0.8015**

| Class | Support | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| **`legitimate`** | 14 | 0.7333 | 0.7857 | 0.7586 |
| **`scam`** | 23 | 0.8636 | 0.8261 | 0.8444 |
| **MACRO AVERAGE** | **37** | **0.7985** | **0.8059** | **0.8015** |

### Confusion Matrix (External Benchmark):
```text
                  Predicted Legitimate    Predicted Scam
True Legitimate            11                   3   (False Positives = 3)
True Scam                   4                  19   (False Negatives = 4)
```

---

## 6. Comparative Analysis: Rules Baseline vs. ML Baseline

| Dimension | Rules Baseline Detector | TF-IDF + Logistic Regression (ML EXP-01) |
| :--- | :--- | :--- |
| **Architecture** | Deterministic Regex & Weighted Heuristics | Sublinear N-gram (1-2) + L2 Linear Classifier |
| **Standard / Benign Benchmark Accuracy ($N=24$)** | 90.9% (20/22 team-curated) | **95.8%** (23/24) |
| **Adversarial Benchmark Accuracy ($N=13$)** | **0.0%** (0/13 caught) | **53.8%** (7/13 caught) |
| **Overall Benchmark Accuracy ($N=37$)** | 59.5% (Tier accuracy) | **81.1%** (Binary mapped accuracy) |
| **Explainability** | High (Exact regex triggers & evidence) | Moderate (Feature weights, n-gram importances) |
| **Inference Latency** | < 1 ms | < 2 ms |

### Key Improvements in ML Model:
1. **Robustness to Obfuscated / Spaced Keywords:**  
   The ML model successfully caught `ADVERSARIAL_OBFUSCATION_001` (`"w-h-a-t-s-a-p-p"`), `ADVERSARIAL_OBFUSCATION_002` (`"t-e-l-e-g-r-a-m"`), and `ADVERSARIAL_OBFUSCATION_003` (`"c-r-e-d-i-t c-a-r-d"`), where exact regex rules completely failed.
2. **Tolerance to Word-Order Perturbations:**  
   The ML model detected inverted phrasing like `"profits guaranteed"` or `"turn 1k into 20k without jeopardy"` because bag-of-ngrams does not require rigid token adjacency.

### Persistent Shared Failure Modes:
1. **Benign Links / URLs:**  
   Both models flagged `BENIGN_010` (*"For full API documentation... visit https://developer.acme.com/docs"*) as suspicious because the presence of imperative visit directives and URLs heavily correlates with phishing in training data.
2. **Weak Indicator Stacking in Benign Contexts:**  
   `ADVERSARIAL_WEAK_STACK_001` (Customer appointment on WhatsApp) and `ADVERSARIAL_WEAK_STACK_002` (Terms of service link) were flagged as scam by the ML model ($P_{\text{scam}} \approx 0.56$), identical to how the rules baseline escalated them to `needs_verification`.

---

## 7. Limitations & Template/Leakage Considerations

1. **Synthetic-Data Distribution Bias:**  
   The synthetic dataset ($N=210$) exhibits clean syntax and consistent grammar. While lexical variety is present, the model has not yet been exposed to noisy, uncurated real-world SMS stream distributions where scam base rates are $<1\%$.
2. **Template-Family Similarity:**  
   Although all 210 samples are deduplicated (Jaccard similarity $\le 0.85$), standard stratified random splitting might allow similar linguistic structures (e.g., standard 2FA SMS phrasing) to appear in both train and test partitions. Future experiments should explore clustered / domain-grouped cross-validation.
3. **No Dynamic Calibration:**  
   The default decision threshold ($0.50$) resulted in one boundary false negative ($P = 0.489$). Threshold tuning or calibration (e.g. Platt scaling) could adjust precision/recall trade-offs.

---

## 8. Exact Commands & Reproducibility

```bash
# 1. Dataset Validation
.\backend\.venv\Scripts\python.exe backend/data/ml/validate_dataset.py

# 2. Pipeline Training (Seed: 42)
.\backend\.venv\Scripts\python.exe backend/ml/train.py --seed 42

# 3. Model Evaluation
.\backend\.venv\Scripts\python.exe backend/ml/evaluate.py
```

---

## 9. Conclusion & Recommendations

- **Experiment 01 Verdict:** **SUCCESSFUL BASELINE ESTABLISHED.**
- **Key Finding:** TF-IDF + Logistic Regression demonstrates superior resilience to paraphrasing and token obfuscation compared to the rules baseline, raising adversarial benchmark performance from $0\%$ to $53.8\%$.
- **Recommendation:** Proceed to Experiment 02 focusing on:
  1. Hybrid rule + ML ensemble architectures (combining rules explainability with ML semantic robustness).
  2. Character n-gram or subword tokenization to further improve resilience to character-level leetspeak/spacing attacks.
  3. Domain-grouped cross-validation to assess out-of-domain generalization.
