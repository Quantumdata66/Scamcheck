# ScamCheck ML Synthetic Dataset Card

**Dataset Version:** `1.0.0-synthetic`  
**Location:** [`backend/data/ml/dataset.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/ml/dataset.json)  
**Creation Date:** October 2026  
**Primary Intended Task:** Initial exploratory training and cross-validation of lightweight NLP classifiers (TF-IDF + Logistic Regression) for ScamCheck binary scam detection and domain scoping.

---

## 1. Dataset Purpose & Scope

The ScamCheck ML synthetic dataset was created to establish an initial, controlled machine learning training foundation during rapid prototype development. Because real-world smishing/phishing corpora often carry privacy, copyright, or unrepresentative noise constraints, this dataset provides a balanced, synthetically generated corpus of suspicious and legitimate messages across our three target scam domains:
1. **Bank & Payment Fraud**
2. **Fake Job Offers**
3. **Unrealistic Investment & Crypto Schemes**
4. **General Benign Communications (`null` category)**

> [!IMPORTANT]
> **Methodological Disclaimer:**  
> This dataset is **entirely synthetic** and was intentionally generated for exploratory modeling and baseline experimentation. **It does NOT represent real-world scam prevalence, real-world class distributions, or empirical communication base rates.** Performance metrics achieved on this dataset must not be claimed as real-world operational accuracy.

---

## 2. Dataset Size & Structural Breakdown

- **Total Sample Count ($N$):** 210 examples
- **Unique Texts:** 210 (100% deduplicated, case/whitespace normalized)
- **Class Balance:** Perfectly balanced (50.0% Scam, 50.0% Legitimate)
- **Isolation:** Strictly separated from the 37-example evaluation benchmark fixture ([`backend/data/evaluation_fixture.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/evaluation_fixture.json)) with zero overlap.

### Distribution by Binary Label
| Label | Count | Percentage | Description |
| :--- | :--- | :--- | :--- |
| **`scam`** | 105 | 50.0% | Messages exhibiting fraudulent deception, credential harvesting, advance-fee demands, or coercive urgency. |
| **`legitimate`** | 105 | 50.0% | Normal, authorized operational notices, career inquiries, receipts, regulatory summaries, or casual chats. |

### Distribution by Target Category
| Category | Count | Percentage | Breakdown (Scam / Legitimate) |
| :--- | :--- | :--- | :--- |
| **`bank_payment`** | 65 | 31.0% | 35 Scam / 30 Legitimate |
| **`fake_job`** | 65 | 31.0% | 35 Scam / 30 Legitimate |
| **`investment`** | 60 | 28.6% | 35 Scam / 25 Legitimate |
| **`null`** (General Benign) | 20 | 9.5% | 0 Scam / 20 Legitimate |
| **TOTAL** | **210** | **100.0%** | **105 Scam / 105 Legitimate** |

---

## 3. Schema & Field Definitions

Each record in `dataset.json` adheres to the following JSON schema:

```json
{
  "id": "ML_SYNTH_001",
  "text": "ALERT: Your Wells Fargo checking account has been suspended due to suspicious activity. Verify your identity at http://wells-secure-portal.com immediately to unlock.",
  "label": "scam",
  "category": "bank_payment",
  "source_type": "synthetic",
  "notes": "Classic bank suspension phishing with unverified domain."
}
```

### Fields:
- **`id` (string, required):** Unique sample identifier prefixed by source type (`ML_SYNTH_xxx`).
- **`text` (string, required):** The full message body to be evaluated.
- **`label` (string, required):** Target binary classification label (`"scam"` or `"legitimate"`).
- **`category` (string or null, required):** Domain classification (`"bank_payment"`, `"fake_job"`, `"investment"`, or `null`).
- **`source_type` (string, required):** Provenance flag (`"synthetic"`, `"team_curated"`, or `"external_anonymized"`).
- **`notes` (string, required):** Contextual annotations detailing the linguistic patterns, adversarial perturbations, or domain signals tested.

---

## 4. Generation Methodology & Diversity Controls

To avoid homogeneous templating, the 210 examples were engineered with intentional linguistic diversity:
1. **Linguistic Framing & Register:** Varied across institutional formal notices, transactional SMS alerts, conversational outreach, and urgent alerts.
2. **Syntactic Variation:** Balanced imperative directives, passive voice constructions (e.g., *"A candidate selection has occurred"*), compound conditionals, and interrogatives.
3. **Message Lengths:** Ranges from short transactional SMS (~10–15 words) to multi-sentence email notifications (~50–80 words).
4. **Adversarial & Boundary Probes:**
   - Word order inversions (e.g., *"guaranteed 100% returns"* instead of *"100% guaranteed returns"*).
   - Synonym substitutions (e.g., *"spaces remain"*, *"remuneration"*, *"allocate capital"*).
   - Legitimate hard cases containing suspicious trigger words in safe contexts (e.g., legitimate 2FA codes with *"do not share"* warnings, SEC regulatory disclaimers *"Past performance is no guarantee of future returns"*, and bank anti-fraud awareness bulletins).

---

## 5. Limitations & Known Biases

1. **Synthetic-Data Bias:** Synthetic texts may feature cleaner grammar, fewer typos, and more explicit intent markers than messy real-world smishing campaigns.
2. **Vocabulary Over-Representation:** Specific high-profile brand names (Chase, Wells Fargo, Amazon, Telegram, WhatsApp) appear frequently to reflect known threat vectors, which could lead a naive classifier to overfit to entity mentions rather than semantic structure.
3. **Zero Population Base Rate Match:** Real-world SMS traffic has a very low base rate of scam messages (<1–5%), whereas this training dataset is artificially balanced (50/50).
4. **Static Threat Snapshot:** Does not capture dynamic, emerging evasion techniques (e.g., novel URL obfuscation, zero-width characters, dynamic QR code phishing).

---

## 6. Privacy & Ethical Considerations

- **No PII:** The dataset contains no genuine personally identifiable information (PII). All names, phone numbers (e.g., `555-xxxx`), addresses, and account numbers are fictionalized or standard placeholders.
- **No Active Malicious Infrastructure:** URLs and domains listed in scam examples use non-routable, fictitious, or example top-level domains (e.g., `wells-secure-portal.com`, `.net`, `.org`, `.cc`) to prevent accidental user exposure or traffic redirection.

---

## 7. Validation & Hygiene

Dataset integrity is enforced using the automated validator [`backend/data/ml/validate_dataset.py`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/ml/validate_dataset.py), which verifies schema conformity, enforces deduplication, and guarantees strict isolation from the benchmark fixture.
