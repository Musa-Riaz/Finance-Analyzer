# Finance Analyzer

Finance Analyzer is a full-stack personal finance platform with a database-first architecture. It supports account authentication, CSV ingestion, transaction persistence, budgeting and planning workflows, anomaly tracking, and dashboard analytics.

The repository currently contains two backend surfaces:

1. Primary app backend (used by the frontend): TanStack Start API routes + ORPC in frontend/src/routes/api.rpc.$.ts with PostgreSQL via Drizzle ORM.
2. Legacy/adjacent analytics backend: FastAPI service under src/finance_analyzer/api for Python ML experimentation and ops endpoints.

The active product flow is database-backed through ORPC and PostgreSQL.

---

## Table of Contents

1. Project Overview
2. Current Architecture
3. Core Modules
4. Authentication Model
5. Data Model and Persistence
6. CSV Ingestion and Analytics Flow
7. Repository Structure
8. Local Setup
9. Environment Variables
10. Runbook
11. API Surfaces
12. Development Commands
13. Troubleshooting
14. Future Improvements

---

## Project Overview

Finance Analyzer provides:

1. Account onboarding and session authentication.
2. Database-backed import and transaction management.
3. Dashboard analytics (summary, monthly trends, category breakdowns, anomalies, forecast) generated from persisted data.
4. Planning modules (budgets, goals, recurring entries, alerts).
5. Transaction operations (create, delete, category rules, monthly analytics, logger).

The app is designed so user-facing analytics survive restarts because data is persisted in PostgreSQL rather than held only in process memory.

---

## Current Architecture

High-level active path:

1. Browser UI (TanStack Router + React) calls ORPC client.
2. ORPC client hits /api/rpc/* route handlers in TanStack Start.
3. ORPC procedures execute server-side business logic.
4. Drizzle ORM reads/writes PostgreSQL.
5. UI updates from TanStack Query invalidation and refetch.

Architecture layers:

1. Presentation layer:
	- frontend/src/routes/*
	- frontend/src/components/*
2. API transport and procedure layer:
	- frontend/src/routes/api.rpc.$.ts
	- frontend/src/orpc/router/index.ts
	- frontend/src/orpc/procedures/*
3. Persistence layer:
	- frontend/src/db/schema.ts
	- frontend/src/db/index.ts
	- drizzle migrations in frontend/drizzle/
4. Optional Python ML/analysis service:
	- src/finance_analyzer/api/*
	- src/finance_analyzer/ml.py and related modules

---

## Core Modules

Primary frontend/backend app module:

1. ORPC auth procedures:
	- frontend/src/orpc/procedures/auth.ts
2. ORPC finance procedures:
	- frontend/src/orpc/procedures/finance.ts
3. Route guards and shell:
	- frontend/src/routes/__root.tsx
4. Client auth/session helpers:
	- frontend/src/lib/auth-client.ts
5. API abstraction for dashboard data:
	- frontend/src/lib/finance-api.ts

Legacy Python analysis module:

1. FastAPI app bootstrap:
	- src/finance_analyzer/api/main.py
2. Python analytics/forecast/anomaly logic:
	- src/finance_analyzer/analyzer.py
	- src/finance_analyzer/ml.py
	- src/finance_analyzer/api/routes/*

---

## Authentication Model

Authentication is implemented in ORPC and persisted in PostgreSQL.

Sign-up/sign-in flow:

1. User submits credentials on /signup or /signin.
2. ORPC auth procedure validates input and credentials.
3. Passwords are hashed with scrypt + salt.
4. Session token is generated, hashed with SHA-256, and stored in user_sessions.
5. Client stores token + user context in localStorage.
6. Root route guard redirects authenticated users to / and unauthenticated users to public routes.

Session propagation:

1. Auth headers include:
	- Authorization: Bearer <token>
	- x-session-token
	- x-user-email
	- x-household-id
	- x-account-id
2. ORPC context resolves active user/tenant from token and membership.

Sign-out:

1. Sidebar sign-out calls auth.signOut.
2. Client clears local session.
3. User is redirected to /landing.

---

## Data Model and Persistence

Database schema is defined in:

1. frontend/src/db/schema.ts

Key entities:

1. Identity and tenancy:
	- users
	- user_credentials
	- user_sessions
	- households
	- household_members
2. Financial records:
	- accounts
	- statement_uploads
	- transactions
	- transaction_enrichments
	- categories
	- category_rules
3. Planning and alerts:
	- budgets
	- budget_allocations
	- goals
	- recurring_transactions
	- alerts

Migrations:

1. Managed by Drizzle Kit under frontend/drizzle/
2. New auth/persistence tables are included in recent migrations.

---

## CSV Ingestion and Analytics Flow

Current primary flow is DB-native in ORPC finance procedures.

Ingestion:

1. User uploads one or more CSV files from dashboard.
2. ORPC finance.upload parses statement CSVs server-side.
3. Transactions are normalized and deduplicated (external hash).
4. Categories are ensured/created where needed.
5. Rows persist into transactions and statement_uploads.
6. Default enrichment rows are added to transaction_enrichments.

Analytics generation (from persisted data):

1. Summary metrics (income, spend, net, totals).
2. Monthly rollups.
3. Category aggregates.
4. Anomaly list from enrichment flags.
5. Forecast from monthly spend trend over persisted history.

This means analytics survive process restarts as long as database data exists.

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
├─ src/
│  └─ finance_analyzer/
│     ├─ analyzer.py
│     ├─ cleaner.py
│     ├─ loader.py
│     ├─ ml.py
│     ├─ visualizer.py
│     └─ api/
│        ├─ main.py
│        ├─ interfaces/models.py
│        └─ routes/
│           ├─ analysis.py
│           ├─ forecast.py
│           └─ upload.py
└─ frontend/
	├─ package.json
	├─ drizzle.config.ts
	├─ drizzle/
	└─ src/
		├─ components/
		├─ db/
		├─ lib/
		├─ orpc/
		├─ routes/
		└─ schemas/
```

---

## Local Setup

Prerequisites:

1. Node.js 20+
2. npm
3. Python 3.13+ (optional if using only DB-first web app features)
4. PostgreSQL-compatible DATABASE_URL (Neon or local Postgres)

### 1) Frontend and DB-first app setup

```powershell
cd frontend
npm install
```

Create frontend env file (example):

```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
```

Run migrations:

```powershell
npm run db:migrate
```

Start app:

```powershell
npm run dev
```

Default URL:

1. http://localhost:3000
	If port is occupied, Vite auto-selects next port.

### 2) Optional Python API setup

From repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m uvicorn finance_analyzer.api.main:app --reload --port 8002 --app-dir src
```

---

## Environment Variables

Frontend app (primary):

1. DATABASE_URL
	- Used by Drizzle/pg for ORPC server-side procedures.

Optional frontend:

1. FINANCE_ALLOW_DEMO_AUTH
2. DEMO_USER_EMAIL
3. DEMO_HOUSEHOLD_NAME
4. DEMO_ACCOUNT_NAME

Python service (optional):

1. Standard FastAPI/uvicorn env as needed.

---

## Runbook

### First run

1. cd frontend
2. npm install
3. set DATABASE_URL in frontend/.env.local
4. npm run db:migrate
5. npm run dev
6. open app, sign up, upload CSVs, verify dashboard metrics

### After schema changes

1. npm run db:generate
2. npm run db:migrate

### Quality checks

1. npm run lint
2. npm run build

---

## API Surfaces

### ORPC (primary)

Mounted at:

1. /api/rpc/*

Main groups:

1. auth
	- signUp
	- signIn
	- me
	- signOut
2. finance
	- upload
	- summary
	- monthly
	- monthlyOverview
	- categories
	- anomalies
	- transactions
	- forecast
	- persisted transactions/categories/rules/budgets/goals/recurring/alerts operations

### FastAPI (optional/legacy)

Mounted at:

1. Python service root routes under src/finance_analyzer/api
2. Includes /ops/metrics and analysis/upload/forecast routes for Python workflows

---

## Development Commands

From frontend/:

1. npm run dev
2. npm run build
3. npm run preview
4. npm run lint
5. npm run test
6. npm run db:generate
7. npm run db:migrate
8. npm run db:push
9. npm run db:pull
10. npm run db:studio

From repository root (Python):

1. python -m uvicorn finance_analyzer.api.main:app --reload --port 8002 --app-dir src

---

## Troubleshooting

### 1) Signup fails with 500

Likely cause:

1. Missing auth migrations.

Fix:

1. cd frontend
2. npm run db:generate
3. npm run db:migrate

### 2) ORPC endpoint returns 404

Likely cause:

1. Procedure name mismatch between route code and ORPC router.

Fix:

1. Ensure procedure is exported in finance/auth procedures.
2. Ensure it is registered in frontend/src/orpc/router/index.ts.

### 3) Dashboard has no data

Likely cause:

1. No persisted transactions yet.

Fix:

1. Sign in.
2. Upload CSV files from dashboard.
3. Re-open dashboard queries.

### 4) Migration command appears stuck at applying migrations

1. Verify database connectivity and sslmode in DATABASE_URL.
2. Re-run npm run db:migrate and check exit code.

---

## Future Improvements

1. Add robust CSV dialect auto-detection and schema validation diagnostics.
2. Add background job queue for large imports and progress tracking.
3. Persist richer anomaly scoring logic and retraining metadata.
4. Introduce role-based authorization checks per procedure group.
5. Add CI pipeline for lint/build/tests/migration drift checks.
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
