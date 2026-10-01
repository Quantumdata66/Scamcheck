# EMSCAD External Evaluation Report: Out-of-Domain Zero-Shot Assessment

**Dataset:** Employment Scam Aegean Dataset (EMSCAD / `amruthjithrajvr/recruitment-scam`)  
**Evaluation Date:** October 2026  
**Runner:** [`backend/ml/evaluate_emscad.py`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/evaluate_emscad.py)  
**Evaluated Models:**  
- `scamcheck_lr_pipeline.joblib` (Word TF-IDF + Logistic Regression, from Experiment 01)  
- `scamcheck_char_lr_pipeline.joblib` (Character TF-IDF + Logistic Regression, from Experiment 02)  
**Summary JSON:** [`backend/ml/results/emscad/emscad_evaluation_summary.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/results/emscad/emscad_evaluation_summary.json)  

---

## 1. Executive Summary

This report documents the zero-shot out-of-domain external evaluation of ScamCheck's Experiment 01 and Experiment 02 machine learning models against the public **EMSCAD** dataset ($N=17,880$ raw job postings, $16,201$ unique postings).

The evaluation was executed with **zero retraining, zero hyperparameter tuning, and zero threshold shifting**, strictly testing how models trained on short inbound conversational smishing messages transfer to long-form formal job board advertisements.

```
Raw EMSCAD CSV (17,880 rows)
            │
            ▼
[ Text Composer & Label Mapper ] ──> (Composed 5 text fields; mapped 't'->scam, 'f'->legitimate)
            │
            ▼
[ Deduplication & Isolation ] ──> (16,201 unique records; 0 overlap with ScamCheck datasets)
            │
            ├───> [ scamcheck_lr_pipeline.joblib ] (Exp 01 Word TF-IDF + LR)
            │
            └───> [ scamcheck_char_lr_pipeline.joblib ] (Exp 02 Char TF-IDF + LR)
            │
            ▼
Side-by-Side Evaluation Metrics & False Positive/Negative Diagnostics
```

---

## 2. Dataset Population & Ingestion Audit

- **Raw Rows Ingested:** 17,880
- **Valid Records Composed:** 17,880 (0 invalid labels, 0 empty texts)
- **Unique Records (Post-Deduplication):** **16,201** (1,679 duplicate re-postings removed)
- **Class Breakdown:**
  - **`legitimate` (`f`):** **15,480** (95.55%)
  - **`scam` (`t`):** **721** (4.45%)
  - **Class Imbalance Ratio:** **21.5 : 1**

### Dataset Isolation & Zero-Contamination Audit:
- **Overlap with Synthetic Dataset ($N=210$):** **0 instances**
- **Overlap with Benchmark Fixture ($N=37$):** **0 instances**

---

## 3. Evaluation Results: Model Comparison vs. Majority Baseline

| Metric | Majority Baseline (Predict All Legit) | EXP-01: Word TF-IDF + LR | EXP-02: Char TF-IDF + LR | Best ML Result |
| :--- | :--- | :--- | :--- | :--- |
| **Accuracy** | 95.55% | 92.52% (14,989 / 16,201) | **95.09%** (15,405 / 16,201) | **EXP-02 (+2.57% over Exp 01)** |
| **Macro F1-Score** | 0.4886 | 0.5572 | **0.5753** | **EXP-02 (+0.0867 over baseline)** |
| **Scam Precision** | 0.00% | 15.47% (110 / 711) | **34.69%** (85 / 245) | **EXP-02 (2.2x higher precision)** |
| **Scam Recall (Sensitivity)**| 0.00% | **15.26%** (110 / 721) | 11.79% (85 / 721) | **EXP-01 (+3.47% recall)** |
| **Scam F1-Score** | 0.00% | 0.1536 | **0.1760** | **EXP-02 (+0.0224)** |
| **Scam PR-AUC** | 0.0445 (Base rate) | 0.1410 (3.2x baseline) | **0.1487** (3.3x baseline) | **EXP-02** |
| **Legitimate Precision** | 95.55% | 96.06% | **96.01%** | EXP-01 |
| **Legitimate Recall** | 100.00% | 96.12% | **98.97%** | **EXP-02** |
| **False Positives ($FP$)** | 0 (Majority) | 601 (3.88%) | **160 (1.03%)** | **EXP-02 (73.4% reduction)** |
| **False Negatives ($FN$)** | 721 (100%) | **611 (84.74%)** | 636 (88.21%) | **EXP-01 (110 caught)** |

---

## 4. Confusion Matrices

### Experiment 01 (Word TF-IDF + Logistic Regression):
```text
                                Predicted Legitimate    Predicted Scam
Actual Legitimate (15,480)            14,879                601   (False Positives)
Actual Scam (721)                        611                110   (True Positives)
```

### Experiment 02 (Character TF-IDF + Logistic Regression):
```text
                                Predicted Legitimate    Predicted Scam
Actual Legitimate (15,480)            15,320                160   (False Positives)
Actual Scam (721)                        636                 85   (True Positives)
```

---

## 5. Comparative Diagnostic Analysis

### A. False Positive Reduction in Experiment 02 (160 vs. 601)
Character-level n-grams (`char_wb`, 3–5) dramatically reduced spurious false positive triggers on long job postings:
1. **Word-Level Over-Triggering:** In Exp 01, common legitimate job posting phrases (e.g. *"no experience required"*, *"apply now"*, *"bonus"*, *"weekly"*) immediately activated word-level features, flagging 601 legitimate postings.
2. **Subword Discrimination:** In Exp 02, character n-grams required higher structural consistency across words, suppressing false positives by **73.4% (from 601 to 160)**.
3. **Remaining False Positives in Exp 02:** Primarily high-turnover canvassing/technician listings (e.g. `emscad_9313`, `emscad_7723` *"INSTALLERS NEEDED... Start Today Paid Mileage"*) that strongly mimic smishing urgency patterns.

### B. False Negatives (636 in Exp 02 vs. 611 in Exp 01)
1. **Sophisticated Corporate Clones:** Fraudulent postings in EMSCAD often duplicate real job descriptions (e.g., *"Health + Environmental Professional"*, *"Registered Nurse"*, *"Strategic Sourcing Engineer"*, `emscad_1204`, `emscad_7484`, `emscad_2969`). The text itself looks 100% formal and professional; the fraud signal was external (e.g., fake company domain or unverified recruiter email in the original ATS listing).
2. **Long-Document Vocabulary Dilution:** In a 600-word posting, subtle scam markers have their TF-IDF signal diluted across hundreds of words of standard boilerplate.

---

## 6. Detailed Domain Mismatch Breakdown

```
┌──────────────────────────────┬───────────────────────────────────────────┬────────────────────────────────────────────┐
│ Dimension                    │ EMSCAD Dataset (Kaggle)                   │ ScamCheck Target Operational Domain        │
├──────────────────────────────┼───────────────────────────────────────────┼────────────────────────────────────────────┤
│ Ingestion Format             │ Multi-section web ATS vacancy postings    │ Short SMS, WhatsApp, Telegram, LinkedIn DM │
│ Average Word Count           │ 350 – 900+ words                          │ 20 – 60 words                              │
│ Fraud Vector                 │ Identity theft via fake corporate portals │ Immediate off-platform pivot, task rebate  │
│                              │ and fraudulent employment agreements      │ fees, upfront equipment deposits           │
│ Vocabulary Density           │ High corporate boilerplate density        │ High imperative action & urgency density   │
│ Era & Threat Landscape      │ 2012 – 2014 (Pre-crypto/task smishing)    │ Contemporary 2026 smishing & crypto scams  │
│ Target Categories            │ `fake_job` only                           │ `bank_payment`, `fake_job`, `investment`   │
└──────────────────────────────┴───────────────────────────────────────────┴────────────────────────────────────────────┘
```

---

## 7. Deduplication & Label Conflict Audit

A rigorous check was conducted across the 17,880 raw EMSCAD records to determine if identical normalized texts ever carry contradictory labels:
- **Total Raw Records:** 17,880
- **Unique Normalized Texts:** 16,201
- **Duplicate Text Instances Sharing Same Label:** 1,679 (100% label consistency)
- **Conflicting Label Groups (Same Text, Different Labels):** **0**
- **Evaluation Population Alignment:** The Majority-Class Baseline, Experiment 01, and Experiment 02 all evaluated the **exact identical population of 16,201 unique records** (15,480 legitimate, 721 fraudulent).

---

## 8. Model Artifact Audit Summary

| Artifact ID | Model Type | Path | Status on EMSCAD Evaluation | Key EMSCAD Metric |
| :--- | :--- | :--- | :--- | :--- |
| **`scamcheck_lr_pipeline.joblib`** | Word N-Gram TF-IDF (1–2) + Logistic Regression (Exp 01) | [`backend/ml/models/scamcheck_lr_pipeline.joblib`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/scamcheck_lr_pipeline.joblib) | **EVALUATED** | Recall: 15.26%, FP: 601, PR-AUC: 0.1410 |
| **`scamcheck_char_lr_pipeline.joblib`** | Character N-Gram TF-IDF (3–5) + Logistic Regression (Exp 02) | [`backend/ml/models/scamcheck_char_lr_pipeline.joblib`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/models/scamcheck_char_lr_pipeline.joblib) | **EVALUATED** | Precision: 34.69%, FP: 160, PR-AUC: 0.1487 |

---

## 9. Conclusions & Strategic Recommendations

1. **Model Generalization Assessment:**  
   Both models significantly outperform the random/majority base rate (PR-AUC $\approx 0.148$ vs. $0.0445$). Exp 02 demonstrates substantially higher precision ($34.69\%$ vs. $15.47\%$) and a **73.4% reduction in false positives**, making it much cleaner for out-of-domain evaluation.
2. **Actionable Recommendations for Future Experiments:**
   - **Do NOT retrain ScamCheck exclusively on EMSCAD:** Doing so would severely skew the model toward long-document corporate vocabulary and destroy performance on short SMS/WhatsApp smishing.
   - **Hybrid Ensembling:** Combine Word TF-IDF and Character TF-IDF in a weighted ensemble to capture both high short-text recall (Exp 01) and subword precision/obfuscation resistance (Exp 02).
