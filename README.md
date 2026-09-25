# ScamCheck

> **Digital Safety, Made Simple.**  
> A fast, explainable decision-support tool for identifying potential scam indicators in suspicious text messages.

---

## Architecture Overview

ScamCheck is organized into a decoupled, modern web stack:

- **Frontend:** React 19 + Vanilla CSS, bundled with Vite.
- **Backend:** Python 3.10+ / FastAPI, Pydantic, and Uvicorn.
- **Detection Engine:** Explainable, rules-based indicator baseline across Bank/Payment scams, Fake Job offers, and Investment schemes.

```text
ScamCheck/
├── api/                      # Vercel serverless integration
│   ├── index.py              # ASGI entry point for Vercel
│   └── requirements.txt      # Serverless runtime dependencies
├── backend/                  # FastAPI Application & Detection Pipeline
│   ├── app/
│   │   ├── main.py           # Application entry & CORS config
│   │   ├── schemas.py        # Pydantic request/response models
│   │   ├── routes/           # /health and /check endpoints
│   │   └── services/         # Normalization, rules engine, detector
│   ├── data/                 # Evaluation fixtures and datasets
│   ├── tests/                # Automated pytest test suites
│   ├── requirements.txt      # Backend Python dependencies
│   ├── BASELINE_DETECTOR.md  # Rules engine documentation
│   ├── DETECTION_SPEC.md     # Indicator taxonomy & specifications
│   └── EVALUATION_BASELINE.md# Adversarial stress-test benchmark report
├── src/                      # React Frontend Source
│   ├── components/           # Modular UI components (Hero, Result, FAQ, etc.)
│   ├── services/             # API client (src/services/api.js)
│   ├── App.jsx               # Root coordinator & state management
│   ├── index.css             # Global styles and resets
│   └── main.jsx              # React mount entry
├── vercel.json               # Full-stack Vercel deployment configuration
├── package.json              # Frontend npm scripts & dependencies
└── vite.config.js            # Vite configuration with local /api proxy
```

---

## Local Development Setup

### 1. Prerequisites
- **Node.js** 18+ (Tested on Node 22)
- **Python** 3.10+ (Tested on Python 3.12)

---

### 2. Start the Backend API

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

- API Base URL: `http://localhost:8000`
- Interactive API Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

---

### 3. Start the Frontend Application

In a separate terminal window:

```bash
# 1. From the repository root
npm install

# 2. Start the Vite dev server
npm run dev
```

- Frontend URL: `http://localhost:5173`

---

## Running Tests & Building

### 1. Run Backend Automated Tests
```bash
cd backend
pytest -v
```

### 2. Run Evaluation Script
```bash
cd backend
python evaluate.py
```

### 3. Build Frontend for Production
```bash
npm run build
```

---

## Deployment Guide (Vercel)

The repository is configured for **zero-config full-stack deployment on Vercel**:

1. Push your repository to GitHub.
2. In Vercel, click **Add New Project** and import the `ScamCheck` repository.
3. Framework Preset: **Vite**.
4. Root Directory: `./` (Default).
5. Build Command: `npm run build` (Default).
6. Output Directory: `dist` (Default).
7. Deploy.

Vercel automatically builds the React SPA and deploys the FastAPI backend as Python serverless functions defined in `api/index.py` via `vercel.json` rewrites.

*For decoupled hosting (e.g. Frontend on Vercel + Backend on Render/Railway), set `VITE_API_BASE_URL=https://your-backend-domain.com` in your Vercel Environment Variables.*
