# Finance Analyzer

Finance Analyzer is a full-stack personal finance analytics project that ingests monthly CSV statements, processes them with a Python/ML pipeline, and presents insights in a professional dashboard UI.

It combines:

- A FastAPI backend for ingestion, analytics, anomaly detection, and forecasting
- A TanStack Start + React frontend for interactive visualization
- A machine learning pipeline for transaction categorization, anomaly detection, and short-term spending forecasts

---

## Table of Contents

1. [What This Project Does](#what-this-project-does)
2. [Core Features](#core-features)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Repository Structure](#repository-structure)
6. [How Data Flows Through the System](#how-data-flows-through-the-system)
7. [Getting Started](#getting-started)
8. [API Reference](#api-reference)
9. [Input CSV Requirements](#input-csv-requirements)
10. [Frontend Commands](#frontend-commands)
11. [Known Limitations](#known-limitations)
12. [Troubleshooting](#troubleshooting)
13. [Deployment and Rollback](#deployment-and-rollback)
14. [Suggested Next Improvements](#suggested-next-improvements)

---

## What This Project Does

Finance Analyzer is designed to answer practical personal-finance questions such as:

- How much did I earn vs spend this month?
- Where is most of my outgoing spend concentrated?
- Which transactions look unusual based on my behavior?
- Is my spending trend rising or falling over the next few months?

The project supports uploading one or more monthly statement CSV files and then generates:

- Portfolio-level summary metrics (income, spend, net, average transaction)
- Monthly trend summaries
- Category-level spending breakdowns
- Anomaly reports with reason text
- A forecast series with trend and error metadata

---

## Core Features

### Backend Analytics

- CSV ingestion through `/upload/`
- Data cleaning and normalization (timestamps, amounts, balances, description cleanup)
- Direction tagging (`IN`/`OUT`)
- Month and label enrichment (`YYYY-MM`, `Mon YYYY`)
- Aggregate analytics (`summary`, `monthly`, `categories`, `transactions`)

### Machine Learning

- Rule-based category assignment from known keyword patterns
- KMeans clustering + TF-IDF for uncategorized transaction text
- Isolation Forest anomaly detection
- Linear regression forecast with leave-one-out error metric

### Frontend Dashboard

- Professional, mobile-responsive dashboard experience
- CSV upload + immediate analytics refresh
- KPI cards for headline metrics
- Recharts visualizations for trends and composition
- Anomaly scatter and flagged transaction list
- Forecast horizon selector (1–12 months)
- Recent transaction table with direction and anomaly tags

---

## Architecture

High-level flow:

1. User uploads one or more monthly CSV files from the frontend.
2. Backend processes all uploaded rows through a cleaning and ML pipeline.
3. Processed DataFrame is stored in memory.
4. Frontend queries backend endpoints for summary, trends, categories, anomalies, transactions, and forecast.
5. Dashboard renders charts and tables from API responses.

### Processing Pipeline

`Upload CSV` -> `Load + Parse` -> `Clean + Normalize` -> `Add Month Columns` -> `Categorize (Rules + KMeans)` -> `Detect Anomalies (IsolationForest)` -> `Aggregate + Forecast`

---

## Tech Stack

### Backend

- Python 3.13+
- FastAPI
- Pandas
- Scikit-learn
- Uvicorn
- Python multipart upload support

### Frontend

- TanStack Start
- React 19
- TanStack Router + TanStack Query
- Tailwind CSS v4
- Recharts
- Lucide icons
- Zod schema validation for API contracts

---

## Repository Structure

```text
finance-analyzer/
├─ README.md
├─ pyproject.toml
├─ main.py
├─ data/
│  ├─ raw/
│  └─ processed/
├─ notebooks/
│  ├─ exploration.ipynb
│  └─ Untitled.ipynb
├─ src/
│  └─ finance_analyzer/
│     ├─ loader.py
│     ├─ cleaner.py
│     ├─ analyzer.py
│     ├─ ml.py
│     ├─ visualizer.py
│     └─ api/
│        ├─ main.py
│        ├─ interfaces/models.py
│        └─ routes/
│           ├─ upload.py
│           ├─ analysis.py
│           └─ forecast.py
└─ frontend/
   ├─ package.json
   └─ src/
      ├─ routes/
      ├─ components/
      ├─ schemas/
      └─ lib/finance-api.ts
```

---

## How Data Flows Through the System

### 1) Ingestion

- Endpoint: `POST /upload/`
- Accepts multiple CSV files in one request
- Reads CSV with parser assumptions defined in `loader.py`

### 2) Cleaning

- Parses `TIMESTAMP` using format `%d/%m/%Y %H:%M`
- Derives `date`, `time`, `day_of_week`, `week`, `month_day`
- Converts comma-separated amounts and balances to numeric values
- Strips multiline/noisy descriptions
- Generates `direction` column from amount sign

### 3) Enrichment + ML

- Adds month columns (`month`, `month_label`)
- Applies rule-based categories first
- Applies TF-IDF + KMeans for uncategorized rows
- Detects anomalies with Isolation Forest and assigns anomaly scores/reasoning

### 4) Aggregation + Forecast

- Summary totals and averages
- Monthly income/spending/net
- Category-level totals/count/averages
- Forecast from monthly spending using linear regression

### 5) Visualization

- Frontend fetches backend endpoints and renders charts/tables
- Dashboard refreshes after upload by invalidating finance queries

---

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 20+
- npm

### 1) Backend setup

From repository root:

```powershell
uv sync
.\.venv\Scripts\Activate.ps1
```

If you are not using `uv`, use pip:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi jupyter matplotlib openpyxl pandas python-multipart scikit-learn seaborn uvicorn
```

Start API server on port `8002` (matches frontend default):

```powershell
python -m uvicorn finance_analyzer.api.main:app --reload --host 0.0.0.0 --port 8002 --app-dir src
```

Health check:

```powershell
Invoke-WebRequest http://localhost:8002/
```

### 2) Frontend setup

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8002/docs`

### 3) Use the app

1. Open dashboard in browser.
2. Upload one or more statement CSV files.
3. Review KPI cards, charts, anomaly list, and forecast section.

---

## API Reference

All responses are JSON and use Pydantic models defined in `src/finance_analyzer/api/interfaces/models.py`.

### Upload

- `POST /upload/`
- Form field: `files` (multi-file CSV upload)
- Returns: `UploadResponse`

Response shape:

```json
{
	"message": "Files uploaded and processed successfully",
	"months_loaded": ["Jan 2026", "Feb 2026"],
	"total_transactions": 1234
}
```

### Analysis

- `GET /analysis/summary` -> `Summary`
- `GET /analysis/monthly` -> `MonthlySummary[]`
- `GET /analysis/categories` -> `CategoryBreakdown[]`
- `GET /analysis/anomalies` -> `Transaction[]` (flagged subset + reason)
- `GET /analysis/transactions` -> `Transaction[]` (all processed rows)

### Forecast

- `GET /forecast/?months_ahead=3`
- Query param: `months_ahead` integer in range `[1, 12]`
- Returns: `ForecastResponse`

If fewer than 2 months are available, forecast returns HTTP 422.

---

## Input CSV Requirements

The loader currently expects bank-export CSVs with this structure:

- First 13 rows are metadata and skipped (`skiprows=13`)
- Required columns:
	- `TIMESTAMP`
	- `TYPE`
	- `DESCRIPTION`
	- `AMOUNT`
	- `BALANCE`
- Timestamp format: `%d/%m/%Y %H:%M`
- Amount and balance may contain commas; they are normalized during cleaning

If a file does not match expected format, upload may fail with HTTP 400.

---

## Frontend Commands

Run these inside `frontend/`:

- `npm run dev` - start local dev server on port 3000
- `npm run build` - production build
- `npm run preview` - preview production build
- `npm run test` - run tests (Vitest)
- `npm run test:e2e:install` - install Playwright Chromium browser
- `npm run test:e2e` - run Playwright E2E smoke tests
- `npm run lint` - run ESLint
- `npm run check` - format + fix lint issues

---

## Configuration Notes

- Frontend API base URL defaults to `http://localhost:8002` in `frontend/src/lib/finance-api.ts`.
- You can override it with:

```bash
VITE_API_BASE_URL=http://localhost:8002
```

- Backend CORS currently allows `http://localhost:3000`.

---

## Known Limitations

1. Processed data is stored in memory (`_processed_df`) and is lost on backend restart.
2. Upload lifecycle is single-process and not designed for multi-user/session isolation yet.
3. CSV parser is schema-specific and may require adaptation for different bank exports.
4. Forecast model is intentionally simple (linear trend baseline).
5. Anomaly contamination default is currently high (`0.5`) and may need tuning for production realism.

---

## Troubleshooting

### Frontend shows API errors after upload

- Ensure backend is running on port `8002`.
- Ensure frontend is running on port `3000` (CORS is configured for this origin).
- Check backend logs for CSV parsing errors.

### Forecast endpoint returns 422

- Upload at least 2 distinct months of transaction data.

### Upload returns 400

- Confirm CSV column names and timestamp format match expected schema.
- Confirm files are actually `.csv`.

---

## Deployment and Rollback

- Use the operational runbook in [DEPLOYMENT_ROLLBACK_PLAYBOOK.md](DEPLOYMENT_ROLLBACK_PLAYBOOK.md) for release, validation, and rollback steps.
- The runbook includes pre-deploy checks, post-deploy smoke tests, rollback triggers, and incident documentation guidance.

---

## Suggested Next Improvements

1. Persist processed data in a database instead of in-memory global state.
2. Add user-level dataset isolation and authentication.
3. Add model/version metadata and configurable anomaly sensitivity.
4. Add backend unit tests and API integration tests.
5. Add CSV schema validation feedback with row-level error reports.
