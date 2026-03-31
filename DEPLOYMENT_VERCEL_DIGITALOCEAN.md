# Deployment Guide: Vercel and DigitalOcean

This repository has two deployable services:

1. Frontend + ORPC API (TanStack Start app) in `frontend/`
2. Python ML API (FastAPI) in `src/finance_analyzer/api/main.py`

## 1) Local Endpoint Configuration

Create `frontend/.env.local` from `frontend/.env.local.example` and set endpoint values.

Required keys:

- `VITE_ORPC_BASE_URL`
- `VITE_PYTHON_API_BASE_URL`
- `VITE_PYTHON_API_DOCS_URL`

Suggested local values:

- `VITE_ORPC_BASE_URL=` (empty for same-origin ORPC)
- `VITE_PYTHON_API_BASE_URL=http://localhost:8002`
- `VITE_PYTHON_API_DOCS_URL=http://localhost:8002/docs`

Also set DB keys in `frontend/.env.local`:

- `DATABASE_URL`
- `DATABASE_URL_POOLER`

For FastAPI CORS, set this env on backend runtime:

- `FRONTEND_ORIGINS=http://localhost:3000,https://your-frontend-domain`

## 2) Deploy on Vercel

### 2.1 Deploy Frontend + ORPC API

Create a Vercel project with Root Directory set to `frontend`.

Build settings:

- Install Command: `npm ci`
- Build Command: `npm run build`

Environment Variables for this project:

- `DATABASE_URL`
- `DATABASE_URL_POOLER`
- `VITE_ORPC_BASE_URL`:
  - Recommended: your frontend URL, for example `https://finance-analyzer-web.vercel.app`
  - If left empty, client falls back to same-origin
- `VITE_PYTHON_API_BASE_URL`: your deployed Python API URL
- `VITE_PYTHON_API_DOCS_URL`: your deployed Python docs URL (`<python-url>/docs`)
- Optional demo keys:
  - `FINANCE_ALLOW_DEMO_AUTH`
  - `DEMO_USER_EMAIL`
  - `DEMO_HOUSEHOLD_NAME`
  - `DEMO_ACCOUNT_NAME`

### 2.2 Deploy Python Backend

Create a second Vercel project using repository root (`.`).

This project uses:

- `vercel.json` (routes all requests to `api/index.py`)
- `api/index.py` (exports FastAPI app)
- `requirements.txt` (Python dependencies)

Environment Variables for backend project:

- `FRONTEND_ORIGINS=https://your-frontend-domain`

Important for Vercel Python bundle limits:

1. Vercel uses `uv.lock` when present. Keep runtime dependencies in `pyproject.toml` minimal.
2. Notebook and plotting dependencies (`jupyter`, `matplotlib`, `seaborn`, test-only packages) should not be in runtime dependencies for serverless deploys.
3. After dependency edits, regenerate lockfile:

```bash
uv lock
```

If your Python function still exceeds Vercel limits, deploy Python backend on DigitalOcean and keep frontend on Vercel.

After deploy, your Python docs should be at:

- `https://<backend-project>.vercel.app/docs`

## 3) Deploy on DigitalOcean App Platform

Create two App Platform services from the same repo.

### 3.1 Frontend Service (Node)

- Source Dir: `frontend`
- Build Command: `npm ci ; npm run build`
- Run Command: `npm run dev -- --host 0.0.0.0 --port 8080`
- HTTP Port: `8080`

Set env vars:

- `DATABASE_URL`
- `DATABASE_URL_POOLER`
- `VITE_ORPC_BASE_URL=https://<your-do-frontend-domain>`
- `VITE_PYTHON_API_BASE_URL=https://<your-do-backend-domain>`
- `VITE_PYTHON_API_DOCS_URL=https://<your-do-backend-domain>/docs`

### 3.2 Backend Service (Python)

- Source Dir: `.`
- Build Command: `pip install -r requirements.txt`
- Run Command: `uvicorn src.finance_analyzer.api.main:app --host 0.0.0.0 --port 8080`
- HTTP Port: `8080`

Set env vars:

- `FRONTEND_ORIGINS=https://<your-do-frontend-domain>`

## 4) Post-Deploy Checklist

1. Open frontend and confirm login, dashboard, imports, and transactions pages load.
2. Confirm ORPC requests succeed at `<frontend-domain>/api/rpc/*`.
3. Open Python docs link from header and verify it points to deployed backend docs.
4. Verify CORS by testing frontend-to-python requests in browser network panel.
5. Confirm DB-backed operations (upload, delete, bulk delete) persist and refresh correctly.

## 5) Quick Rollback

1. Revert Vercel/DigitalOcean project env vars to previous values.
2. Redeploy previous stable commit.
3. If needed, set `VITE_ORPC_BASE_URL` to the last known working frontend URL.
4. Keep `FRONTEND_ORIGINS` aligned with the currently active frontend hostname.
