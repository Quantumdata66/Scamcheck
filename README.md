# ScamCheck 🛡️

> **Digital Safety, Made Simple.**  
> An explainable, text-only decision-support system for identifying potential warning signs in suspicious messages, explaining detected indicators, and providing actionable safety guidance.

[![Live Application](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=flat&logo=vercel)](https://scam-check1.vercel.app/)
[![API Docs](https://img.shields.io/badge/OpenAPI%20Docs-FastAPI-009688?style=flat&logo=fastapi)](https://scam-check1.vercel.app/docs)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61DAFB?style=flat&logo=react)](https://react.dev/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Pydantic%20v2-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-88%20Passed-brightgreen?style=flat&logo=pytest)](backend/tests/)

---

## 1. Project Overview & Problem Statement

Digital deception—including SMS smishing, fake recruitment offers, and high-yield investment schemes—targets individuals daily across mobile messaging and social platforms. These fraudulent communications exploit artificial urgency, emotional manipulation, and deceptive payment instructions to force impulsive actions before victims can verify authenticity.

**ScamCheck** provides a lightweight, accessible screening tool designed to help users evaluate suspicious messages before taking risky actions (such as clicking unknown links, sharing one-time passcodes, or transferring funds).

When a user submits text from an SMS, email, WhatsApp, Telegram, or social media message, ScamCheck:
1. Normalizes and screens the text against a structured taxonomy of known scam indicators and manipulation patterns.
2. Assigns an explainable, multi-tier risk level (`low`, `needs_verification`, or `high`).
3. Outlines the specific warning signs detected in plain language with zero technical jargon.
4. Generates contextual, protective safety steps to prevent credential theft and financial loss.

> [!IMPORTANT]
> **Decision Support Notice:** ScamCheck is an assistive screening tool, not an investigative or law enforcement authority. It provides automated pattern assessment to aid user vigilance. It does **not** prove that a message or sender is fraudulent, nor does a low-risk result guarantee that a message is authentic or safe.

---

## 2. Live Demo & API Documentation

The full-stack application is deployed live on Vercel:

- 🌐 **Web Application:** [https://scam-check1.vercel.app/](https://scam-check1.vercel.app/)
- 📖 **Interactive OpenAPI Documentation:** [https://scam-check1.vercel.app/docs](https://scam-check1.vercel.app/docs)
- 🩺 **Health Check Endpoint:** [https://scam-check1.vercel.app/health](https://scam-check1.vercel.app/health)

---

## 3. How It Works: Request Lifecycle

```text
  User Text Input (React 19 + Vite Frontend)
                     │
                     ▼  HTTP POST /check (JSON: {"text": "..."})
  FastAPI Service (Pydantic v2 Schema & Boundary Validation)
                     │
                     ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Production Engine: RulesBaselineDetector                               │
  ├────────────────────────────────────────────────────────────────────────┤
  │ 1. Text Normalization ────> Strip control chars, unfold leetspeak      │
  │ 2. Indicator Detection ───> Regex patterns + negative 2FA guards       │
  │ 3. Evidence Weighting ────> Weighted signals (Strong: 3.0, Med: 1.5)   │
  │ 4. Multi-Factor Risk ─────> Threshold heuristics ('low', 'needs', 'hi')│
  │ 5. Guidance Synthesis ────> Category summary, indicators, safety steps │
  └────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
  Structured JSON Assessment Response
                     │
                     ▼
  Rendered in React Interactive Assessment Component
```

---

## 4. Production Architecture & Rules-Based Detector

The production application is powered by an explainable, deterministic detection engine (`RulesBaselineDetector` in [`backend/app/services/detector.py`](backend/app/services/detector.py)):

### 5-Step Detection Pipeline

1. **Text Normalization ([`normalization.py`](backend/app/services/normalization.py)):**
   - Strips non-printable control characters and collapses redundant whitespace.
   - Normalizes Unicode homoglyphs, symbol substitutions, and common leetspeak variants (e.g., `p@ssw0rd`, `0TP`).
   - Folds casing for consistent downstream pattern matching.

2. **Indicator Detection & Negative 2FA Guards ([`rules.py`](backend/app/services/rules.py)):**
   - Matches text against curated regular expression patterns across three core threat domains:
     - `bank_payment` (**Bank & Payment Impersonation**): Unauthorized transaction alerts, account suspension threats, credential/OTP harvesting, and safe-account redirection.
     - `fake_job` (**Fake Recruitment Schemes**): Unrealistic daily pay, immediate hiring without interviews, task-rebate schemes, upfront equipment fees, and Telegram/WhatsApp recruitment hops.
     - `investment` (**High-Yield Investment Scams**): Guaranteed risk-free returns, crypto trading bots, high-pressure countdown timers, and unsolicited signal groups.
   - **Negative 2FA Guards:** Legitimate authentication messages often contain words like "security code" alongside standard security disclaimers (*"Do not share this code"*, *"If you did not request this"*). Negative guards recognize these disclaimers to prevent false alarms on legitimate 2FA notifications.

3. **Indicator Evidence Weighting ([`rules.py`](backend/app/services/rules.py) & [`detector.py`](backend/app/services/detector.py)):**
   - Each detected indicator carries a signal weight:
     - **Strong ($3.0$):** High-confidence scam cues (e.g., direct requests for OTP/passwords, guaranteed risk-free daily returns, upfront training/equipment fees).
     - **Medium ($1.5$):** Moderate warning signs (e.g., redirecting to off-platform recruiters, urgent account restriction threats).
     - **Weak ($0.5$):** Contextual or low-specificity cues (e.g., generic payment terms, URL shorteners).

4. **Multi-Factor Risk Level Determination ([`detector.py`](backend/app/services/detector.py)):**
   - Evaluates indicator counts, strength combinations, and dominant category scores:
     - **`high` ("Multiple warning signs detected"):** $\ge 2$ strong indicators match, or $1$ strong $+ 1$ medium indicator match, or $1$ strong indicator matches with dominant category score $\ge 3.0$, or $\ge 2$ medium indicators match with dominant category score $\ge 3.0$, or total evidence score reaches $\ge 3.5$.
     - **`low` ("No obvious warning signs detected"):** Zero indicators triggered, or only a single weak indicator present ($\le 0.5$ total score) with zero strong or medium signals.
     - **`needs_verification` ("Needs further verification"):** The safe default tier for isolated cues, moderate unconfirmed patterns, or ambiguous language requiring user verification.

5. **Actionable Guidance Generation ([`guidance.py`](backend/app/services/guidance.py)):**
   - Synthesizes clear, plain-language explanations of why the message was flagged.
   - Generates category-specific protective steps (e.g., calling the official bank number on the back of a card, refusing off-platform communication hops, never disclosing OTPs).

---

## 5. Risk Levels & Threat Taxonomy

| Risk Level | Display Label | Condition & Criteria |
| :--- | :--- | :--- |
| **`high`** | *Multiple warning signs detected* | Multiple high-confidence cues converge ($\ge 2$ strong, or strong + medium, or score $\ge 3.5$). |
| **`needs_verification`** | *Needs further verification* | Isolated medium signal, ambiguous payment terms, or unverified link shorteners. |
| **`low`** | *No obvious warning signs detected* | No known indicators detected, or single low-weight contextual cue ($\le 0.5$). |

### Supported Threat Categories
- **`bank_payment`**: Banking alerts, account lock threats, credential phishing, payment redirect scams.
- **`fake_job`**: High-pay task schemes, instant hiring, upfront equipment fees, off-platform communication.
- **`investment`**: Guaranteed crypto/forex returns, automated trading bots, insider VIP signals.
- **`null`**: General or uncategorized warning signs when cues span multiple domains or lack a dominant category.

---

## 6. API Reference

### 1. Health Check
- **Path:** `GET /health` (or `GET /api/v1/health`)
- **Response (HTTP 200):**
  ```json
  {
    "status": "healthy",
    "version": "0.1.0"
  }
  ```

---

### 2. Message Analysis
- **Path:** `POST /check` (or `POST /api/v1/check`)
- **Headers:** `Content-Type: application/json`

#### Request Payload
```json
{
  "text": "URGENT: Your bank debit card has been blocked due to suspicious activity. Reply with your OTP immediately to restore access."
}
```
*(Note: `"message"` is also accepted as an alias for `"text"`.)*

#### Successful Response (HTTP 200)
```json
{
  "risk_level": "high",
  "risk_label": "Multiple warning signs detected",
  "summary": "This message exhibits strong warning signs commonly associated with bank or payment impersonation.",
  "category": "bank_payment",
  "explanation": "This message was flagged because it solicits sensitive credentials (such as PINs, passwords, or one-time security codes) and it applies artificial pressure threatening account suspension or immediate penalties.",
  "indicators": [
    "Request for sensitive credentials or security codes",
    "Urgent request for account action"
  ],
  "safety_guidance": [
    "Contact your bank directly using the official number on the back of your card or via their verified app.",
    "Never share one-time passcodes (OTPs), PINs, or online banking passwords with anyone.",
    "Do not transfer money to 'safe' or 'holding' accounts under any circumstances."
  ]
}
```

#### Validation Error (HTTP 422)
- Enforces a **2,000 character maximum limit** and rejects empty or whitespace-only submissions.

#### Example cURL Command
```bash
curl -X POST "https://scam-check1.vercel.app/check" \
     -H "Content-Type: application/json" \
     -d '{"text": "Congratulations! You are hired for the Remote Data Entry role ($400/day). Message our recruiter on Telegram @hire_dept now."}'
```

---

## 7. Testing & Quality Verification

The backend automated test suite contains **88 tests** with 100% pass rate:

```bash
# Run the test suite
pytest backend/tests -v
```

### Test Coverage Breakdown
- **`test_detector.py` (21 tests):** Verifies category assignment, indicator weight scoring, threshold boundary heuristics, and guidance generation.
- **`test_adversarial.py` (19 tests):** Validates normalization under obfuscation (character spacing, leetspeak substitutions, negative 2FA guard disclaimers).
- **`test_check.py` (9 tests):** Verifies FastAPI route handlers, Pydantic input schemas, 2,000-character boundary limits, and HTTP error responses.
- **`test_emscad_evaluation.py` (30 tests):** Tests text composition, label mapping, and dataset deduplication logic for external benchmarks.
- **`test_emscad_experiment03.py` (8 tests):** Tests EMSCAD 70/15/15 train/val/test split integrity and model loading.
- **`test_health.py` (1 test):** Verifies `/health` operational endpoint.

---

## 8. Offline Machine Learning Experiments

ScamCheck conducted three standalone, reproducible machine learning experiments in `backend/ml/` to evaluate statistical modeling alongside the rules baseline.

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
│            │                             │                           │ Short Lures ($N=37$)     │ **51.35%** Acc, 30.43% Recall  │
└────────────┴─────────────────────────────┴───────────────────────────┴──────────────────────────┴────────────────────────────────┘
```

> [!IMPORTANT]
> **Dataset Separation & Metric Interpretation:**
> - **Exp 01 & 02:** Evaluated on synthetic short-message partitions ($N=42$) and an adversarial fixture ($N=13$).
> - **Exp 03:** Trained on $11,340$ EMSCAD long-form corporate job descriptions and evaluated on a held-out test set of $2,431$ postings (108 fraudulent, 4.44% prevalence).
> - **Cross-Modality Evaluation:** When the EMSCAD-trained model (Exp 03) was evaluated on short conversational job lures ($N=37$), **scam recall dropped to 30.43%** (identifying only 7 of 23 scams) due to severe length and vocabulary mismatch. (30.43% represents scam recall on the short-message diagnostic partition, not overall model accuracy).

### Experiment Reports:
- [ML Experiment 01: Baseline Word TF-IDF Classifier](backend/ml/ML_EXPERIMENT_01.md)
- [ML Experiment 02: Character-Level Obfuscation-Resistant Classifier](backend/ml/ML_EXPERIMENT_02.md)
- [ML Experiment 03: EMSCAD Corporate Recruitment Classifier & Transfer](backend/ml/ML_EXPERIMENT_03.md)
- [EMSCAD External Zero-Shot Evaluation Report](backend/ml/EMSCAD_EXTERNAL_EVALUATION.md)
- [ML Pipeline & Training Guide](backend/ml/README.md)

---

## 9. Why ML Experiments Do Not Power Production

**The live ScamCheck application is powered strictly by the deterministic `RulesBaselineDetector`. The statistical ML models are offline research experiments.**

This architectural decision is driven by three engineering requirements:

1. **Deterministic Explainability & User Trust:** In consumer safety and fraud decision support, users need explicit, auditable reasons why a message was flagged. The rules engine provides exact evidence mapping with zero probabilistic hallucination.
2. **Zero-Latency Serverless Deployment:** The rules engine runs instantly in serverless environments without loading heavy vectorizer matrices or model weights into memory.
3. **Cross-Modality Transfer Limits:** As demonstrated empirically in Experiment 03, models trained on long corporate job descriptions fail on short conversational SMS/chat lures (dropping to 30.43% scam recall). Deploying statistical models across open-ended user inputs without domain-matched training data introduces unacceptable false-negative risks.

---

## 10. Limitations & Responsible Use

1. **Text-Only Screening:** ScamCheck analyzes only submitted text. It does not crawl live websites, inspect SSL certificates, check DNS records, or query carrier databases.
2. **No Link Visiting or Sandboxing:** The engine statically detects the presence of URLs and link shorteners. It does **not** click or execute links.
3. **Never Share Credentials:** Legitimate institutions never request PINs, passwords, or one-time passcodes over direct text or chat replies.
4. **No Defamation or Absolute Proof:** ScamCheck is an assistive screening tool and must not be used as definitive legal or forensic proof of fraud.
5. **Low Risk $\neq$ Guaranteed Authenticity:** Fraudsters continually evolve phrasing. If a communication involves money or credentials, verify the sender independently via an official channel.

---

## 11. Future Improvements

- **Hybrid Ensemble Architecture:** Integrate character n-gram confidence scores alongside the rules baseline for soft indicator scoring on unseen vocabulary.
- **Expanded Real-World Smishing Corpus:** Collect and annotate diverse mobile messaging lures across regional payment systems and SMS formats.
- **API Rate Limiting & Abuse Prevention:** Implement token-bucket rate limiting on the `/check` endpoint.
- **Browser Extension:** Develop an on-device Chrome extension for instant email and chat screening.

---

## 12. Tech Stack

- **Frontend:** React 19, Vite, React Icons, Vanilla CSS (Design Tokens & Responsive UI)
- **Backend:** FastAPI, Pydantic v2, Uvicorn, Python 3.12
- **Testing:** Pytest, HTTPX
- **ML Experimentation (Offline):** Scikit-Learn, Joblib, NumPy, Pandas
- **Deployment:** Vercel (Unified Frontend + Python Serverless Runtime via `api/index.py` & `vercel.json`)

---

## 13. Local Setup & Development

### Prerequisites
- **Node.js** 18+ (Node 20 or 22 recommended)
- **Python** 3.10+ (Python 3.12 recommended)
- **Git**

### 1. Clone Repository
```bash
git clone https://github.com/Quantumdata66/Scamcheck.git
cd Scamcheck
```

### 2. Backend Setup (FastAPI)
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run automated tests
pytest tests -v

# Start backend server
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### 3. Frontend Setup (React + Vite)
In a new terminal window:
```bash
# From repository root
npm install

# Start Vite development server
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 14. Project Structure

```text
Scamcheck/
├── api/                                # Vercel serverless entrypoint
│   ├── index.py                        # ASGI application bridge
│   └── requirements.txt                # Serverless deployment dependencies
├── backend/                            # FastAPI Application & ML Experiments
│   ├── app/                            # Production web service
│   │   ├── main.py                     # FastAPI app factory & CORS configuration
│   │   ├── schemas.py                  # Pydantic request & response models
│   │   ├── routes/                     # /health and /check endpoint routes
│   │   │   ├── check.py
│   │   │   └── health.py
│   │   └── services/                   # Production rules detection engine
│   │       ├── detector.py             # RulesBaselineDetector implementation
│   │       ├── guidance.py             # Plain-language explanation & guidance generator
│   │       ├── normalization.py        # Text cleaning, homoglyph & leetspeak normalizer
│   │       └── rules.py                # Regex indicators, weights & negative 2FA guards
│   ├── data/                           # Datasets & evaluation fixtures
│   │   ├── evaluation_fixture.json     # 37-example diagnostic fixture
│   │   ├── external/emscad/            # EMSCAD dataset (fake_job_postings.csv)
│   │   └── ml/                         # Synthetic dataset (dataset.json, DATASET_CARD.md)
│   ├── ml/                             # Offline ML research & pipelines
│   │   ├── models/                     # Saved joblib pipelines, split manifests, & reports
│   │   ├── results/                    # Validation metrics & evaluation summaries
│   │   ├── preprocessing.py            # Feature transformation routines
│   │   ├── train.py                    # Experiment 01 training script
│   │   ├── train_char.py               # Experiment 02 training script
│   │   ├── train_emscad.py             # Experiment 03 training script
│   │   ├── evaluate.py                 # Evaluation benchmark runner
│   │   ├── evaluate_emscad.py          # EMSCAD external evaluation runner
│   │   ├── ML_EXPERIMENT_01.md         # Experiment 01 report
│   │   ├── ML_EXPERIMENT_02.md         # Experiment 02 report
│   │   ├── ML_EXPERIMENT_03.md         # Experiment 03 report
│   │   ├── EMSCAD_DATA_PROFILE.md      # EMSCAD dataset profile
│   │   ├── EMSCAD_EXTERNAL_EVALUATION.md# EMSCAD external evaluation report
│   │   └── README.md                   # ML architecture & replication guide
│   ├── tests/                          # Automated pytest test suites (88 tests)
│   │   ├── test_adversarial.py
│   │   ├── test_check.py
│   │   ├── test_detector.py
│   │   ├── test_emscad_evaluation.py
│   │   ├── test_emscad_experiment03.py
│   │   └── test_health.py
│   ├── requirements.txt                # Backend dependencies
│   ├── BASELINE_DETECTOR.md            # Rules engine implementation spec
│   ├── DETECTION_SPEC.md               # Indicator taxonomy & technical spec
│   └── EVALUATION_BASELINE.md          # Baseline detector evaluation report
├── src/                                # React Frontend Source
│   ├── components/                     # Modular UI components (Hero, Result, FAQ, etc.)
│   ├── services/                       # API client (src/services/api.js)
│   ├── App.jsx                         # Main application coordinator
│   ├── index.css                       # Design tokens & styles
│   └── main.jsx                        # React root mount
├── vercel.json                         # Unified full-stack Vercel configuration
├── package.json                        # Frontend npm dependencies & scripts
├── vite.config.js                      # Vite build & local API proxy configuration
└── README.md                           # Main repository documentation
```

---

## 15. License & Data Provenance

- **License:** Created as part of the BuildLabs Capstone Project. Distributed for educational and non-commercial research purposes.
- **Synthetic ML Dataset ($N=210$):** Curated and validated specifically for ScamCheck's short-message baseline experiments ([`backend/data/ml/DATASET_CARD.md`](backend/data/ml/DATASET_CARD.md)).
- **EMSCAD Dataset ($N=17,880$ raw / $16,201$ unique):** Employment Scam Aegean Dataset (Vidros et al., 2017), derived from Workable job postings and sourced via public research mirrors.
