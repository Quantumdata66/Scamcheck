# ScamCheck Baseline Evaluation & Adversarial Analysis

**Phase:** Baseline Evaluation & Adversarial Stress Testing  
**Component Evaluated:** `RulesBaselineDetector` (`backend/app/services/detector.py`)  
**Evaluation Dataset:** `backend/data/evaluation_fixture.json`  
**Evaluation Runner:** `backend/evaluate.py`  
**Status:** Evaluation Completed (Pre-ML Benchmarking)

---

## 1. Evaluation Methodology & Scope

To rigorously test the deterministic rules-based baseline before introducing Machine Learning, we established a structured evaluation framework that tests the system against standard scam examples, legitimate communications, and deliberate adversarial perturbations.

> **Crucial Methodological Distinction:**  
> The metrics presented in this document are derived from a **small, curated development fixture (N=37)** designed specifically to expose boundary failures and adversarial vulnerabilities. These numbers represent **heuristic stress-test benchmarks**, not real-world population accuracy.

---

## 2. Dataset Composition & Source Types

The evaluation fixture consists of 37 carefully annotated examples across three source types:

```
┌───────────────────────────────┬───────┬────────────────────────────────────────────────────────┐
│ Source Type                   │ Count │ Description & Testing Purpose                          │
├───────────────────────────────┼───────┼────────────────────────────────────────────────────────┤
│ team-curated (Standard Scams) │ 12    │ Typical smishing, fake job offers, and crypto schemes  │
│ team-curated (Legitimate)     │ 10    │ Real-world benign messages (2FA, receipts, jobs, news) │
│ synthetic-adversarial         │ 2     │ Academic news & educational scam awareness texts       │
│ adversarial-synthetic         │ 13    │ Deliberate evasion attacks (synonyms, typos, passive)  │
├───────────────────────────────┼───────┼────────────────────────────────────────────────────────┤
│ TOTAL                         │ 37    │                                                        │
└───────────────────────────────┴───────┴────────────────────────────────────────────────────────┘
```

### Distribution by Target Category:
- **`bank_payment`:** 9 examples (4 clear scams, 5 adversarial/legitimate)
- **`fake_job`:** 8 examples (4 clear scams, 4 adversarial)
- **`investment`:** 6 examples (4 clear scams, 2 adversarial)
- **`null` (Benign / Unclassified):** 14 examples (10 benign, 4 adversarial edge cases)

---

## 3. Baseline Performance Results

### Summary Metrics on Evaluation Fixture (N=37)

| Metric | Result | Interpretation |
| :--- | :--- | :--- |
| **Overall Risk Label Accuracy** | **59.5%** (22/37) | Strong on standard messages, vulnerable to adversarial variations. |
| **Category Classification Accuracy** | **78.4%** (29/37) | High reliability when domain indicators are detected. |
| **Team-Curated Standard Accuracy** | **90.9%** (20/22) | Baseline accurately handles standard, expected patterns. |
| **Adversarial Subset Accuracy** | **0.0%** (0/13) | Exposes deterministic regex limitations to paraphrasing. |

---

### Classification Metrics per Risk Tier

```
┌─────────────────────┬─────────┬───────────┬────────┬──────────┐
│ Risk Tier           │ Support │ Precision │ Recall │ F1-Score │
├─────────────────────┼─────────┼───────────┼────────┼──────────┤
│ low                 │ 14      │ 0.579     │ 0.786  │ 0.667    │
│ needs_verification  │ 9       │ 0.417     │ 0.556  │ 0.476    │
│ high                │ 14      │ 1.000     │ 0.429  │ 0.600    │
├─────────────────────┼─────────┼───────────┼────────┼──────────┤
│ MACRO AVERAGE       │ 37      │ 0.665     │ 0.590  │ 0.581    │
└─────────────────────┴─────────┴───────────┴────────┴──────────┘
```

### Confusion Matrix (Risk Tiers)
```text
True \ Predicted      low    needs_verification    high
low                   11     3                     0
needs_verification    4      5                     0
high                  4      4                     6
```

---

## 4. Error Analysis

### A. False Positives (3 Instances)
*Instances where a benign/legitimate message was incorrectly escalated to `needs_verification`:*

1. **`BENIGN_010` (Technical Documentation URL):**
   - **Text:** *"For full API documentation and integration guides, please visit our developer portal at https://developer.acme.com/docs."*
   - **Triggered Indicator:** `GEN_SUSPICIOUS_LINK`
   - **Reason:** The regex heuristic `visit` + `https://` triggered a link prompt warning despite the lack of urgency.
2. **`ADVERSARIAL_WEAK_STACK_001` (Benign Customer Appointment):**
   - **Text:** *"Dear Customer, please message us on WhatsApp if you have any questions regarding your upcoming appointment."*
   - **Triggered Indicators:** `GEN_ANONYMOUS_SENDER` (0.5) + `GEN_CHANNEL_HOPPING` (0.5)
   - **Reason:** Two weak non-scam signals combined to reach the `1.0` threshold for `needs_verification`.
3. **`ADVERSARIAL_WEAK_STACK_002` (Terms of Service Update):**
   - **Text:** *"Attention User, please click the link below to view our updated terms of service: https://acme.org/terms"*
   - **Triggered Indicators:** `GEN_SUSPICIOUS_LINK` + `GEN_ANONYMOUS_SENDER`
   - **Reason:** Benign policy link matched imperative link pattern without malicious context.

---

### B. False Negatives (8 Instances)
*Instances where a scam message was classified as `low` (missed detection):*

1. **`SCAM_JOB_003` (Task-based rebate):**
   - **Text:** *"Earn passive income online! Like 5 YouTube videos to earn $50 commission. Deposit funds to unlock higher level task rebates."*
   - **Reason:** Regex expected `like youtube videos` without the intervening number `5`.
2. **`ADVERSARIAL_SYNONYM_001` (Bank Credential Harvesting via Synonyms):**
   - **Text:** *"Kindly convey the 6-digit passcode sent to your handset so that we can reactivate your restricted banking profile without delay."*
   - **Reason:** Phrasing used *'convey passcode to handset'* instead of *'reply with OTP'*, and *'without delay'* instead of *'urgent'*.
3. **`ADVERSARIAL_SYNONYM_002` (Fake Job via Archaic Phrasing):**
   - **Text:** *"Acquire immense remuneration of 500 USD each morning by completing uncomplicated phone evaluations with nil prerequisites."*
   - **Reason:** Phrasing used *'immense remuneration'* and *'uncomplicated evaluations'*.
4. **`ADVERSARIAL_SYNONYM_003` (Investment Scheme via Formal Terms):**
   - **Text:** *"Assured financial yield of 200% on all digital currency allocations. Zero hazard guaranteed capital gain."*
   - **Reason:** Used *'financial yield'* and *'zero hazard'* instead of *'guaranteed profit'*.
5. **`ADVERSARIAL_OBFUSCATION_002` (Punctuation Obfuscation):**
   - **Text:** *"Selected for remote role! Contact our HR team on W.h.a.t.s.A.p.p at +123456789 to get hired."*
   - **Reason:** Dotted spelling `W.h.a.t.s.A.p.p` evaded keyword match.
6. **`ADVERSARIAL_PASSIVE_INDIRECT_001` (Passive Voice Credential Solicit):**
   - **Text:** *"A temporary restriction has been instituted regarding your card. Submission of the security verification number is requested to lift this constraint."*
   - **Reason:** Passive phrasing *'submission is requested'* evaded imperative verb regex.
7. **`ADVERSARIAL_PASSIVE_INDIRECT_002` (Indirect Upfront Fee):**
   - **Text:** *"Upon receipt of $50 for onboarding administrative processing, the work-from-home computing equipment will be dispatched."*
   - **Reason:** Subordinate clause *'Upon receipt of $50 for onboarding processing'* evaded direct command regex.
8. **`ADVERSARIAL_SPACING_CASING_001` (Spaced Word Obfuscation):**
   - **Text:** *" u R g E n T : Y O U R B A N K A C C O U N T I S L O C K E D ! R E P L Y W I T H O T P N O W ! "*
   - **Reason:** Single-letter space insertion evaded word-boundary token matching.

---

### C. Category & Tier Discrepancies (4 Instances)
*Instances correctly flagged as suspicious, but assessed at a lower tier (`needs_verification` instead of `high`) due to partial pattern evasion:*
- **`ADVERSARIAL_OBFUSCATION_001`:** `p-a-s-s-w-0-r-d` and `0TP` were missed, but account lockout was caught.
- **`ADVERSARIAL_OBFUSCATION_003`:** `G_U_A_R_A_N_T_E_E_D` was missed, but crypto bot was caught.
- **`ADVERSARIAL_MIXED_001` & `_002`:** Cross-category dilution split evidence weights.

---

## 5. Summary of Baseline Detector Weaknesses

```
┌──────────────────────────────┬────────────────────────────────────────────────────────┐
│ Vulnerability Type           │ Mechanism & Observed Failure Pattern                   │
├──────────────────────────────┼────────────────────────────────────────────────────────┤
│ 1. Synonym Sensitivity       │ Cannot generalize beyond curated dictionary tokens     │
│                              │ ('convey passcode' vs 'send OTP').                     │
├──────────────────────────────┼────────────────────────────────────────────────────────┤
│ 2. Syntactic Rigidity        │ Fails on passive voice or inverted sentence clauses    │
│                              │ ('Submission is requested' vs 'Submit your PIN').      │
├──────────────────────────────┼────────────────────────────────────────────────────────┤
│ 3. Character Obfuscation     │ Spaced letters ('u R g E n T') and leetspeak           │
│                              │ ('p-a-s-s-w-0-r-d') evade token matchers.              │
├──────────────────────────────┼────────────────────────────────────────────────────────┤
│ 4. Benign URL Sensitivity    │ Over-flags neutral URLs containing words like 'visit'. │
├──────────────────────────────┼────────────────────────────────────────────────────────┤
│ 5. Weak Signal Accumulation  │ Stacking two benign weak signals triggers false        │
│                              │ 'needs_verification'.                                  │
└──────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 6. Readiness for Machine Learning Comparison

### Conclusion: **READY FOR ML BENCHMARKING**

The rules-based baseline provides a **high-precision (100% precision on High tier in fixture)**, deterministic anchor with distinct, well-documented failure modes.

### Recommended Next Progression:
1. **Retain the baseline untouched** as the deterministic benchmark.
2. Introduce a lightweight NLP/ML classifier (e.g. TF-IDF + Logistic Regression/Linear SVM, or fine-tuned compact transformer) to address:
   - Semantic synonym generalization.
   - Passive and indirect grammatical structures.
   - Robustness against character perturbations.
3. Compare the baseline rules vs ML model on a unified test split.
