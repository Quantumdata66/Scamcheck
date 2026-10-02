# ScamCheck Backend API

FastAPI backend service and detection engine for the ScamCheck application.

---

## Overview

The ScamCheck backend provides an explainable API for evaluating suspicious text messages. It analyzes incoming text for warning signs across three primary threat domains (bank impersonation, fake job offers, and investment scams), classifies the risk level into one of three tiers (`low`, `needs_verification`, or `high`), and returns actionable safety advice.

The production service uses a deterministic rules engine ([`RulesBaselineDetector`](app/services/detector.py)) with zero inference latency. Machine learning experiments are maintained as standalone research artifacts in [`ml/`](ml/README.md).

---

## Project Structure

```text
backend/
├── app/
│   ├── __init__.py           # Package marker
│   ├── main.py               # FastAPI application factory and CORS configuration
│   ├── schemas.py            # Pydantic request and response models
│   ├── routes/
│   │   ├── __init__.py       # Routes package marker
│   │   ├── health.py         # GET /health endpoint
│   │   └── check.py          # POST /check endpoint
│   └── services/
│       ├── __init__.py       # Services package marker
│       ├── detector.py       # RulesBaselineDetector implementation
│       ├── guidance.py       # Explanation and safety guidance generator
│       ├── normalization.py  # Text cleaning and URL extraction
│       └── rules.py          # Regex indicator taxonomy and 2FA guards
├── data/                     # Datasets and benchmark fixtures
│   ├── evaluation_fixture.json
│   ├── external/emscad/
│   └── ml/
├── ml/                       # Standalone machine learning experiments (Exp 01, 02, 03)
├── tests/                    # Automated test suites (88 tests)
│   ├── test_adversarial.py
│   ├── test_check.py
│   ├── test_detector.py
│   ├── test_emscad_evaluation.py
│   ├── test_emscad_experiment03.py
│   └── test_health.py
├── requirements.txt          # Backend Python dependencies
├── BASELINE_DETECTOR.md      # Rules engine specification
├── DETECTION_SPEC.md         # Indicator taxonomy definition
└── README.md                 # Backend documentation (This file)
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+ (Tested on Python 3.12)
- `pip` package manager

### 2. Create and Activate a Virtual Environment

From inside the `backend` directory:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate on macOS or Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Development Server

Start the FastAPI development server with Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

- Local API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc API Documentation: `http://localhost:8000/redoc`

---

## Running Automated Tests

Run the complete backend test suite using `pytest`:

```bash
# Run all tests with verbose output
pytest tests -v
```

Current test coverage: **88 / 88 tests passing** (0 failures).

---

## API Reference

### 1. Health Check

- **Method:** `GET`
- **Path:** `/health`
- **Response (`200 OK`):**
  ```json
  {
    "status": "healthy",
    "version": "0.1.0"
  }
  ```

---

### 2. Message Analysis

- **Method:** `POST`
- **Path:** `/check`
- **Request Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "text": "URGENT: Your debit card has been blocked. Reply with your OTP immediately to restore access."
  }
  ```
  *Note: The field name `"message"` is also accepted as an alternative to `"text"`.*

- **Validation Constraints:**
  - `text` or `message` is required.
  - Input cannot be empty or contain only whitespace.
  - Maximum length: 2,000 characters.

- **Response Body (`200 OK`):**
  ```json
  {
    "risk_level": "high",
    "risk_label": "Multiple warning signs detected",
    "summary": "This message exhibits strong warning signs commonly associated with bank or payment impersonation.",
    "category": "bank_payment",
    "explanation": "This message was flagged because it solicits sensitive credentials (such as PINs, passwords, or one-time security codes) and it applies artificial pressure threatening account suspension or immediate penalties...",
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

- **Error Response (`422 Unprocessable Entity`):**
  Returned if input validation fails (e.g. whitespace-only text or input exceeding 2,000 characters).

---

## Operational Boundaries

1. **Text-Only Pattern Matching:** The backend analyzes only the text content provided. It does not perform active network requests, DNS lookups, or URL fetching.
2. **Stateless Processing:** Incoming messages are processed in-memory during the request lifecycle. The backend maintains no database storage or persistent message logs.
3. **Decision Support:** Outputs provide automated risk indicators to aid vigilance, not forensic proof of fraud.
