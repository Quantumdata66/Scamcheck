# ScamCheck Rules-Based Baseline Detector

**Component:** Heuristic Baseline Detection Engine  
**Module Path:** `backend/app/services/detector.py`  
**Specification:** `backend/DETECTION_SPEC.md`  
**Status:** Implemented & Verified

---

## 1. Purpose & Architectural Role

The Rules-Based Baseline Detector serves as the foundational detection engine for ScamCheck. Its primary objective is to establish an **explainable, transparent, deterministic benchmark** against which future machine learning models or hybrid pipelines can be quantitatively and qualitatively compared.

### Key Objectives
1. Provide instant, zero-latency detection across the three MVP scam domains (`bank_payment`, `fake_job`, `investment`).
2. Map raw text inputs directly to human-interpretable indicators and actionable safety guidance.
3. Validate the end-to-end API pipeline before training and integrating statistical classifiers.
4. Establish clear false-positive boundaries on legitimate communications.

---

## 2. Detection Pipeline Architecture

The detection service processes text sequentially through five modular stages:

```
[Raw Message Text]
       ↓
1. Normalization (whitespace collapsing, casing normalization, URL extraction)
       ↓
2. Contextual Indicator Matchers (16 curated rules with negation guards)
       ↓
3. Category Scoring (aggregating domain-specific evidence weights)
       ↓
4. Risk Assessment (evaluating indicator strength, convergence, and score)
       ↓
5. Guidance & Explanation Generation (dynamic, evidence-tied narrative)
       ↓
[Structured CheckResponse]
```

---

## 3. Indicator Taxonomy & Implementation Approach

Indicators are defined as structured objects (`DetectedIndicator`) pairing semantic definitions with contextual evidence.

### Supported Indicators

| Code | Domain | Strength | Semantic Trigger Condition |
| :--- | :--- | :--- | :--- |
| `BANK_URGENT_ACTION` | `bank_payment` | Medium | Combines account lockout/threat with immediate urgency. |
| `BANK_CREDENTIAL_HARVEST` | `bank_payment` | Strong | Demands PIN, OTP, password, CVV (guarded against 2FA alerts). |
| `BANK_UNAUTHORIZED_ALERT` | `bank_payment` | Medium | Fake debit/charge notification with urgent dispute call to action. |
| `BANK_PAYMENT_REDIRECT` | `bank_payment` | Strong | Directs funds to 'safe' accounts, gift cards, or crypto transfers. |
| `JOB_UNREALISTIC_PAY` | `fake_job` | Medium | Exorbitant daily/hourly rates for unskilled/remote tasks. |
| `JOB_NO_INTERVIEW_HIRE` | `fake_job` | Medium | Claims candidate is selected/hired without screening. |
| `JOB_UPFRONT_PAYMENT` | `fake_job` | Strong | Demands upfront fees for onboarding, kits, or training. |
| `JOB_TASK_REBATE` | `fake_job` | Medium | Task-based commission schemes requiring deposits. |
| `JOB_OFF_PLATFORM` | `fake_job` | Weak | Directs candidate to personal chat apps for hiring discussions. |
| `INV_GUARANTEED_RETURNS` | `investment` | Strong | Promises risk-free, 100% guaranteed, or doubled returns. |
| `INV_URGENCY_FOMO` | `investment` | Medium | Uses limited spots or countdown timers to rush investments. |
| `INV_CRYPTO_PLATFORM` | `investment` | Medium | Solicits deposits into unverified automated bots or mining pools. |
| `INV_INSIDER_MENTOR` | `investment` | Medium | Promotes insider trading signals, crypto gurus, or managed accounts. |
| `GEN_SUSPICIOUS_LINK` | General | Medium | Urgent directive to click an unverified link. |
| `GEN_ANONYMOUS_SENDER` | General | Weak | Generic impersonal greeting at message start. |
| `GEN_CHANNEL_HOPPING` | General | Weak | Directs conversation to personal chat apps. |

---

## 4. Internal Scoring & Risk Assessment Logic

### Strength Weights
- **Strong (`3.0` points):** High-confidence scam markers (e.g., upfront fees, credential demands, guaranteed returns).
- **Medium (`1.5` points):** Moderate scam markers requiring context (e.g., urgent action, unrealistic pay).
- **Weak (`0.5` points):** Contextual signals that should never trigger high risk in isolation (e.g., anonymous greeting).

### Category Attribution
Category scores are aggregated across all triggered indicators. The category with the highest accumulated score is assigned as the dominant `category`. If no category-specific indicators are triggered, `category` is `null`.

### Risk Tier Thresholds
- **`high` (`Multiple warning signs detected`):**
  - Triggered when: `num_strong >= 2`, OR (`num_strong >= 1` AND `num_medium >= 1`), OR (`num_medium >= 2` within a single dominant category), OR `total_score >= 3.5`.
- **`needs_verification` (`Needs further verification`):**
  - Triggered when: A single strong or medium indicator is present, or multiple weak signals produce `total_score >= 1.0`.
- **`low` (`No obvious warning signs detected`):**
  - Triggered when: No indicators are detected, or only 1 weak signal is observed (`total_score <= 0.5`).

---

## 5. False-Positive Protections

To avoid naive keyword traps, the detector includes explicit negative heuristics:
1. **2FA Exclusions:** Legitimate 2FA security texts ("Your verification code is 123456. Do not share this code.") contain negation guards (`never share`, `do not share`, `will not ask`) that suppress `BANK_CREDENTIAL_HARVEST`.
2. **Standard Financial Disclaimers:** Texts containing regulatory warnings ("Past performance is no guarantee of future returns") suppress `INV_GUARANTEED_RETURNS`.
3. **Corporate Job Postings:** Standard annual salaries ($100k–$150k/year) with professional requirements do not trigger `JOB_UNREALISTIC_PAY`.
4. **Isolated Chat Mentions:** Casual mentions of WhatsApp or Telegram without recruiter or urgency context do not trigger channel hopping alerts.

---

## 6. Why This is a Baseline (Not Production Fraud Verification)

1. **Deterministic Rule Limits:** Pattern-based regex matching cannot understand subtle adversarial paraphrasing, slang, or novel fraud vectors.
2. **No Link or Entity Verification:** The detector cannot verify whether a URL points to a legitimate banking portal or a phishing mirror.
3. **Absence of Context:** Analyzes isolated message snippets without access to prior conversation history or sender reputation.
4. **Benchmark Role:** This baseline provides the clear, interpretable foundation that will be used to evaluate dataset distributions and future lightweight machine learning models.
