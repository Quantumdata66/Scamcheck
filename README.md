# ScamCheck

> **Digital Safety, Made Simple.**  
> An explainable, text-only decision-support tool for identifying potential warning signs in suspicious messages and providing clear safety guidance.

[![Live Application](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=flat&logo=vercel)](https://scam-check1.vercel.app)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61DAFB?style=flat&logo=react)](https://react.dev/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Pydantic-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-88%20Passed-brightgreen?style=flat&logo=pytest)](backend/tests/)

---

## 1. Project Overview

Digital deception, including SMS smishing, fake job offers, and high-yield investment scams, frequently targets individuals across mobile messaging and social media platforms. These deceptive messages often exploit artificial urgency, emotional pressure, or misleading payment instructions to prompt impulsive actions.

**ScamCheck** is a lightweight, text-only screening tool designed to help users evaluate suspicious messages before taking risky actions. When a user pastes text from an SMS, email, WhatsApp, Telegram, or social media message, ScamCheck:

1. Evaluates the text against a structured taxonomy of known scam indicators and communication patterns.
2. Assigns an explainable, multi-tier risk assessment (`low`, `needs_verification`, or `high`).
3. Outlines the specific warning signs detected in plain language.
4. Provides actionable, protective safety guidance to prevent credential theft and financial loss.

> [!IMPORTANT]
> **Decision Support Notice:** ScamCheck is an assistive screening tool, not an investigative authority. It provides automated pattern assessment to aid user vigilance. It does **not** prove that a message or sender is fraudulent, nor does a low-risk result guarantee that a message is authentic or safe.

---

## 2. Live Demo

The application is deployed live on Vercel:

- **Live URL:** [https://scam-check1.vercel.app/](https://scam-check1.vercel.app/)
- **Interactive API Documentation:** [https://scam-check-eight.vercel.app/docs](https://scam-check1.vercel.app/docs)

*Note: The live service relies on the deployed serverless backend API being reachable.*

---

## 3. Current Verified Features

- **Text-Only Message Screening:** Analyzes raw message text pasted directly into the web interface.
- **Three Core Threat Categories:**
  - `bank_payment` (**Bank & Payment Scams**): Unauthorized transaction alerts, urgent account suspension threats, OTP/credential harvesting, and safe-account transfer redirections.
  - `fake_job` (**Fake Job Offers**): Unrealistic daily pay, immediate hiring without interviews, task-rebate schemes, upfront equipment/training fees, and off-platform recruitment hops.
  - `investment` (**Investment Scams**): Guaranteed risk-free profits, automated crypto trading bots, high-pressure FOMO countdowns, and unsolicited insider signal gurus.
  - `null` (**General / Uncategorized**): Assigned when detected cues do not clearly match a single dominant threat category.
- **Robust Input Validation:**
  - Maximum input length enforced at **2,000 characters**.
  - Rejects empty strings and whitespace-only submissions with clear validation feedback.
  - Dual field acceptance: supports both `text` and `message` in JSON request payloads.
- **Three-Tier Risk Level Classification:**
  - `"low"`: Display label *"No obvious warning signs detected"*
  - `"needs_verification"`: Display label *"Needs further verification"*
  - `"high"`: Display label *"Multiple warning signs detected"*
- **Structured, Explainable Output:** Every response returns a structured assessment containing summary reasoning, matched warning indicators, and specific protective next steps.

---

## 4. How It Works

### Production Architecture & Request Flow

The live application is powered by an explainable, deterministic detection engine (`RulesBaselineDetector`):

```text
User Text Input (React Frontend)
         │
         ▼  HTTP POST /check (JSON: {"text": "..."})
FastAPI Backend (Pydantic Request Validation)
         │
         ▼
[ Step 1: Text Normalization ] ────> Strip control chars, collapse whitespace, unfold leetspeak
         │
         ▼
[ Step 2: Indicator Detection ] ───> Regex patterns + negative 2FA guard disclaimers
         │
         ▼
[ Step 3: Indicator Weighting ] ───> Evidence weights (Strong: 3.0, Medium: 1.5, Weak: 0.5) per category
         │
         ▼
[ Step 4: Multi-Factor Risk ] ─────> Decision heuristics & category thresholds ('low', 'needs_verification', 'high')
         │
         ▼
[ Step 5: Guidance Generation ] ───> Contextual summary, indicator explanations, safety guidance
         │
         ▼
Structured JSON Response ──────────> Rendered in React Result Component
```

### Detection & Risk Assessment Logic

The detection engine executes a 5-step explainable pipeline:

1. **Text Normalization (`normalization.py`):** Strips non-printable characters, collapses redundant whitespace, normalizes Unicode symbols and leetspeak variants, and folds casing for consistent pattern matching.
2. **Indicator Detection & Negative Guards (`rules.py`):** Matches text against curated regular expressions across threat categories (`bank_payment`, `fake_job`, `investment`) and cross-cutting signals (such as artificial urgency or suspicious link patterns). To prevent false alarms on legitimate authentication messages, **negative 2FA guards** recognize standard security disclaimers (e.g., *"Do not share this code"*, *"If you did not request this"*) and suppress spurious credential-harvesting triggers.
3. **Indicator Evidence Weights (`rules.py` & `detector.py`):** Each detected indicator carries a predefined evidence weight representing signal strength:
   - **Strong ($3.0$):** High-confidence scam cues (e.g., requesting OTP/password credentials, guaranteed risk-free daily returns, upfront training/equipment fees).
   - **Medium ($1.5$):** Moderate warning signs (e.g., redirecting to Telegram/WhatsApp recruiters, unsolicited trading gurus, urgent account suspension threats).
   - **Weak ($0.5$):** Contextual or low-specificity cues (e.g., generic payment terms, URL shorteners).

   > [!NOTE]
   > **Evidence Weights vs. Final Risk Level:** The weights (3.0, 1.5, 0.5) measure *individual indicator evidence strength* within specific threat categories. They are not a simple linear score sum for the final classification. The final risk level is determined through convergence heuristics, category-specific thresholds, and signal combination rules.
4. **Multi-Factor Risk Level Determination (`detector.py`):** Evaluates indicator counts, strength combinations, and dominant category scores:
   - **`high` ("Multiple warning signs detected"):** Assigned when multiple high-confidence signals converge, specifically when $\ge 2$ strong indicators match, or $1$ strong $+ 1$ medium indicator match, or $1$ strong indicator matches with dominant category score $\ge 3.0$, or $\ge 2$ medium indicators match with dominant category score $\ge 3.0$, or $\ge 3$ medium indicators match, or total evidence score reaches $\ge 3.5$.
   - **`low` ("No obvious warning signs detected"):** Assigned when no indicators are triggered, or only a single weak indicator is present ($\le 0.5$ total score) with zero strong or medium signals.
   - **`needs_verification` ("Needs further verification"):** The safe default tier for single isolated indicators, moderate unconfirmed cues, or ambiguous patterns that require independent user verification.
5. **Guidance & Explanation Generation (`guidance.py`):** Synthesizes plain-language explanations of why the message was flagged and produces category-specific, actionable safety steps (e.g., contacting the bank via an official card number, refusing off-platform communication, or never sharing one-time passcodes).

### Production Detector vs. Experimental ML Models

- **Production Engine (`RulesBaselineDetector`):** Powers the live application and API. It provides 100% deterministic, explainable rule matching with zero inference latency and explicit evidence tracing.
- **Machine Learning Experiments (Exp 01, Exp 02, Exp 03):** Researched and evaluated separately in `backend/ml/`. These models serve as empirical benchmarks for statistical n-gram representations and cross-domain transfer. **The experimental ML models do not power the live production website.**

---

## 5. Technology Stack

Verified from project configuration files ([`package.json`](package.json), [`requirements.txt`](requirements.txt), [`backend/requirements.txt`](backend/requirements.txt), and [`vercel.json`](vercel.json)):

### Frontend
- **Framework:** React 19 (`^19.2.8`)
- **Build Tool:** Vite (`^8.3.0`)
- **Icons:** React Icons (`^5.7.0`)
- **Styling:** Vanilla CSS (Custom design system with responsive cards, badges, and modals)

### Backend & API
- **Web Framework:** FastAPI (`>=0.115.0`)
- **Data Validation:** Pydantic v2 (`>=2.9.0`)
- **ASGI Server:** Uvicorn (`>=0.30.0`)
- **Language:** Python 3.10+ (Tested on Python 3.12)
- **Serverless Integration:** Vercel Python Runtime (`api/index.py` via `vercel.json` rewrites)

### Testing & Machine Learning
- **Test Framework:** Pytest (`>=8.3.0`), HTTPX (`>=0.27.0`)
- **ML Frameworks:** Scikit-Learn, Joblib, NumPy (Used for ML experimentation under `backend/ml/`)

---

## 6. Getting Started

### Prerequisites
- **Node.js** 18+ (Node 20 or 22 recommended)
- **Python** 3.10+ (Python 3.12 recommended)
- **Git**

---

### Local Development Setup

Run the backend and frontend in separate terminal windows:

#### Terminal 1: Backend (FastAPI)

```bash
# 1. Navigate to backend folder
cd backend

# 2. Create and activate a virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the FastAPI development server
uvicorn app.main:app --reload --port 8000
```

- Local API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

#### Terminal 2: Frontend (React + Vite)

```bash
# 1. From the repository root
npm install

# 2. Start the Vite dev server
npm run dev
```

- Local Web App: `http://localhost:5173`

---

### Environment Variables

| Variable | Scope | Default (Development) | Purpose |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Frontend | `http://localhost:8000` (in `dev`) | Overrides API target when frontend and backend are hosted on different domains. |

*In production unified Vercel deployments, `VITE_API_BASE_URL` is omitted so the frontend uses same-origin relative paths.*

---

## 7. API Reference

### 1. Health Check

Checks operational readiness and API version.

- **Method:** `GET`
- **Path:** `/health` (or `/api/v1/health`)
- **Response (HTTP 200):**
  ```json
  {
    "status": "healthy",
    "version": "0.1.0"
  }
  ```

---

### 2. Analyze Message

Analyzes suspicious text and returns risk assessment, detected indicators, and guidance.

- **Method:** `POST`
- **Path:** `/check` (or `/api/v1/check`)
- **Headers:** `Content-Type: application/json`

#### Request Payload
```json
{
  "text": "URGENT: Your Wells Fargo debit card has been blocked due to suspicious activity. Reply with your OTP code immediately to restore access."
}
```

*Note: The field name `"message"` is also accepted as an alternative to `"text"`.*

#### Successful Response (HTTP 200)
```json
{
  "risk_level": "high",
  "risk_label": "Multiple warning signs detected",
  "summary": "This message exhibits strong warning signs typical of Bank & Payment scams.",
  "category": "bank_payment",
  "explanation": "The message creates artificial urgency around an account restriction and requests sensitive security credentials (like an OTP or password). Legitimate financial institutions do not demand one-time passcodes over direct text replies.",
  "indicators": [
    "Urgent account action required",
    "Request for sensitive credentials"
  ],
  "safety_guidance": [
    "Do not click any links or reply to the message.",
    "Do not share one-time passcodes (OTPs), PINs, or passwords with anyone.",
    "Contact your bank directly using the official phone number on the back of your card or their official app."
  ]
}
```

#### Validation Error Response (HTTP 422)
```json
{
  "detail": "Message exceeds maximum length of 2000 characters."
}
```

#### Example cURL Request
```bash
curl -X POST "http://localhost:8000/check" \
     -H "Content-Type: application/json" \
     -d '{"text": "Congratulations! You are hired for the Remote Data Entry job ($400/day). Message our recruiter on Telegram @hire_dept now."}'
```

---

## 8. Testing & Quality Verification

### 1. Backend Automated Test Suite

The backend test suite covers API routing, edge cases, Pydantic validation, deterministic rules, adversarial scenarios, and ML dataset integrity.

```bash
# Run all backend tests
pytest backend/tests -v
```

**Status:** **88 / 88 tests passing** (0 failures).
- `test_adversarial.py` (19 tests): Tests obfuscation, leetspeak, spacing, and negation guards.
- `test_check.py` (9 tests): Tests schema validation, 2000-character boundary, and HTTP error handling.
- `test_detector.py` (21 tests): Tests category detection, risk level scoring, and guidance generation.
- `test_emscad_evaluation.py` (30 tests): Tests text composition, label mapping, and deduplication logic.
- `test_emscad_experiment03.py` (8 tests): Tests EMSCAD 70/15/15 split integrity and model loading.
- `test_health.py` (1 test): Tests `/health` endpoint status.

### 2. Frontend Production Build Check

```bash
# Verify frontend build compiles without errors
npm run build
```

---

## 9. Machine Learning Experiments

ScamCheck conducted three standalone, reproducible machine learning experiments to evaluate statistical modeling approaches alongside the rules baseline.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ SCAMCHECK MACHINE LEARNING EXPERIMENT MATRIX                                                                                     │
├────────────┬─────────────────────────────┬───────────────────────────┬──────────────────────────┬────────────────────────────────┤
│ Experiment │ Architecture & Vectorizer   │ Training Dataset          │ Evaluation Dataset       │ Key Evaluation Metrics         │
├────────────┼─────────────────────────────┼───────────────────────────┼──────────────────────────┼────────────────────────────────┤
│ **Exp 01** │ Word TF-IDF (1–2) + LogReg  │ Synthetic Short ($N=168$) │ Synthetic Test ($N=42$)  │ **97.62%** Acc, 95.24% Recall  │
│            │                             │                           │ Adversarial ($N=13$)     │ **53.85%** Acc (Adv. Baseline) │
│            │                             │                           │ EMSCAD ($N=16,201$)      │ **52.88%** Acc (Zero-Shot)     │
├────────────┼─────────────────────────────┼───────────────────────────┼──────────────────────────┼────────────────────────────────┤
│ **Exp 02** │ Char-WB TF-IDF (3–5)+LogReg │ Synthetic Short ($N=168$) │ Synthetic Test ($N=42$)  │ **90.48%** Acc, 85.71% Recall  │
│            │                             │                           │ Adversarial ($N=13$)     │ **61.54%** Acc (Adv. Highest)  │
│            │                             │                           │ EMSCAD ($N=16,201$)      │ **54.49%** Acc (Zero-Shot)     │
├────────────┼─────────────────────────────┼───────────────────────────┼──────────────────────────┼────────────────────────────────┤
│ **Exp 03** │ Word Unigram (1–1) + LogReg │ EMSCAD Long ($N=11,340$)  │ EMSCAD Test ($N=2,431$)  │ **97.41%** Acc, 86.11% Recall  │
│            │                             │                           │ Diagnostic ($N=37$)      │ **51.35%** Acc, 30.43% Recall  │
└────────────┴─────────────────────────────┴───────────────────────────┴──────────────────────────┴────────────────────────────────┘
```

> [!IMPORTANT]
> **Dataset Separation & Metric Interpretation:**
> - **Distinct Evaluation Distributions:** Experiments 01 and 02 were evaluated on a small held-out synthetic test set ($N=42$) and a 13-example adversarial fixture. In contrast, Experiment 03 was evaluated on a large held-out split of $2,431$ real-world EMSCAD corporate recruitment postings (108 scam examples, 4.44% test base rate).
> - **Non-Comparable Metrics:** Because the underlying dataset distributions, text lengths (30-word SMS messages vs. 500-word corporate job descriptions), and test sample sizes differ significantly, **these accuracy figures are not directly comparable to one another**.
> - **Experimental vs. Production Performance:** These metrics reflect offline evaluations on specific curated or held-out dataset partitions. They do **not** represent verified accuracy or performance guarantees for live production traffic across heterogeneous, open-ended real-world message streams.

### Experiment Summaries & Reports:

1. **[ML Experiment 01: Baseline Word TF-IDF Classifier](backend/ml/ML_EXPERIMENT_01.md)**
   Evaluated word n-grams (1–2) on a 210-example synthetic dataset ($N_{\text{train}}=168, N_{\text{test}}=42$). Achieved **97.62% accuracy**, 95.24% scam recall (100.0% scam precision, 100.0% legitimate recall), and 0.9762 macro F1 on the held-out synthetic test partition, improving adversarial detection to 53.85% (compared to 0% for the initial rules baseline).
2. **[ML Experiment 02: Character-Level Obfuscation-Resistant Classifier](backend/ml/ML_EXPERIMENT_02.md)**
   Evaluated subword character n-grams (`char_wb`, 3–5) on the identical synthetic split ($N_{\text{train}}=168, N_{\text{test}}=42$). Achieved **90.48% accuracy**, 85.71% scam recall (94.74% scam precision, 95.24% legitimate recall), and 0.9045 macro F1 on the synthetic test partition and the highest adversarial robustness (**61.54%**), successfully capturing spaced and underscore-obfuscated keywords (e.g., `G_U_A_R_A_N_T_E_E_D`).
3. **[ML Experiment 03: EMSCAD-Trained Fake-Job Classifier & Transfer](backend/ml/ML_EXPERIMENT_03.md)**
   Trained directly on $11,340$ EMSCAD long-form recruitment ads. Achieved **97.41% accuracy, 86.11% scam recall (93/108), 65.96% scam precision, and 0.8616 PR-AUC** on the held-out EMSCAD test partition ($N=2,431$, 4.44% scam prevalence). Validation metrics: 97.24% accuracy, 0.8524 PR-AUC ($N=2,430$).
4. **[EMSCAD External Zero-Shot Evaluation Report](backend/ml/EMSCAD_EXTERNAL_EVALUATION.md)**
   Evaluated Experiments 01 and 02 zero-shot across $16,201$ unique EMSCAD postings to test generalization across domain shifts.
5. **[ML Documentation & Pipeline Guide](backend/ml/README.md)**
   Complete guide to running training, evaluation, and split verification scripts.

### Key Cross-Modality Transfer Finding:
When the EMSCAD-trained model (Exp 03) was evaluated on short conversational messages ($N=37$), scam recall dropped from **86.11% to 30.43%** due to structural modality mismatch (short 30-word SMS messages vs. 500-word corporate postings). Consequently, Experiment 03 serves as a specialized classifier for long-form job advertisements and is **not** suitable as a general ScamCheck smishing detector.

---

## 10. Limitations & Safe Use

To ensure responsible usage, please keep the following operational boundaries in mind:

1. **Text-Only Pattern Matching:** ScamCheck analyzes only the text content provided. It does **not** perform live network crawling, verify website DNS/SSL certificates, check caller ID databases, or sandbox URLs.
2. **No Link Visiting:** The application identifies the presence of links and suspicious URL patterns statically. It does **not** click, open, or fetch URLs.
3. **Never Share Sensitive Credentials:** Legitimate banks, employers, and organizations will never ask for your passwords, PINs, or 2FA one-time passcodes (OTPs) over SMS or unverified chats.
4. **No Defamation or Final Proof:** Do not use ScamCheck output to definitively label named individuals, employers, or entities as fraudulent.
5. **Low Risk $\neq$ Guaranteed Safe:** Threat actors constantly evolve their phrasing. If a message seems unusual or asks for money, verify the sender independently via an official, trusted channel regardless of the tool's rating.

---

## 11. Project Structure

```text
ScamCheck/
├── api/                                # Vercel serverless integration
│   ├── index.py                        # ASGI application bridge for Vercel
│   └── requirements.txt                # Serverless deployment requirements
├── backend/                            # FastAPI Application & ML Experiments
│   ├── app/                            # Production web service
│   │   ├── main.py                     # FastAPI app factory & CORS setup
│   │   ├── schemas.py                  # Pydantic request & response models
│   │   ├── routes/                     # /health and /check route handlers
│   │   │   ├── check.py
│   │   │   └── health.py
│   │   └── services/                   # Production rules detection engine
│   │       ├── detector.py             # RulesBaselineDetector implementation
│   │       ├── guidance.py             # Explanation and safety guidance generator
│   │       ├── normalization.py        # Text cleaning and casing normalizer
│   │       └── rules.py                # Regex indicators and category scoring
│   ├── data/                           # Datasets & evaluation fixtures
│   │   ├── evaluation_fixture.json     # 37-example isolated benchmark fixture
│   │   ├── external/emscad/            # EMSCAD public dataset (fake_job_postings.csv)
│   │   └── ml/                         # Synthetic ML dataset (dataset.json, DATASET_CARD.md)
│   ├── ml/                             # ML experiments & pipelines
│   │   ├── models/                     # Saved joblib pipelines, split manifests, & predictions
│   │   ├── results/                    # Validation metrics and evaluation summaries
│   │   ├── preprocessing.py            # Feature cleaning routines
│   │   ├── train.py                    # Experiment 01 training runner
│   │   ├── train_char.py               # Experiment 02 training runner
│   │   ├── train_emscad.py             # Experiment 03 training runner
│   │   ├── evaluate.py                 # Evaluation benchmark runner
│   │   ├── evaluate_emscad.py          # EMSCAD external evaluation runner
│   │   ├── ML_EXPERIMENT_01.md         # Experiment 01 report
│   │   ├── ML_EXPERIMENT_02.md         # Experiment 02 report
│   │   ├── ML_EXPERIMENT_03.md         # Experiment 03 report
│   │   ├── EMSCAD_DATA_PROFILE.md      # EMSCAD dataset profile
│   │   ├── EMSCAD_EXTERNAL_EVALUATION.md# EMSCAD external evaluation report
│   │   └── README.md                   # ML architecture documentation
│   ├── tests/                          # Automated pytest test suites (88 tests)
│   │   ├── test_adversarial.py
│   │   ├── test_check.py
│   │   ├── test_detector.py
│   │   ├── test_emscad_evaluation.py
│   │   ├── test_emscad_experiment03.py
│   │   └── test_health.py
│   ├── requirements.txt                # Backend Python dependencies
│   ├── BASELINE_DETECTOR.md            # Rules engine implementation spec
│   ├── DETECTION_SPEC.md               # Indicator taxonomy & technical spec
│   └── EVALUATION_BASELINE.md          # Baseline detector evaluation report
├── src/                                # React Frontend Source
│   ├── components/                     # Modular UI components (Hero, Result, FAQ, Header, etc.)
│   ├── services/                       # API client (src/services/api.js)
│   ├── App.jsx                         # Main React application coordinator
│   ├── index.css                       # Global styles & design system tokens
│   └── main.jsx                        # React root mount
├── vercel.json                         # Unified full-stack Vercel configuration
├── package.json                        # Frontend npm dependencies & scripts
├── vite.config.js                      # Vite build & local API proxy configuration
└── README.md                           # Main repository documentation (This file)
```

---

## 12. License & Data Provenance

- **Project License:** Created as part of the BuildLabs Capstone Project (Cohort 2). Distributed for educational and non-commercial research purposes.
- **Synthetic ML Dataset ($N=210$):** Curated and validated specifically for ScamCheck's short-message baseline experiments ([`backend/data/ml/DATASET_CARD.md`](backend/data/ml/DATASET_CARD.md)).
- **EMSCAD Dataset ($N=17,880$ raw / $16,201$ unique):** Employment Scam Aegean Dataset, published by C. Vidros, C. Kolias, G. Kambourakis, and L. Akoglu (2017), derived from Workable job postings (2012–2014) and sourced via public research mirrors.
