# Deployment and Rollback Playbook

This playbook defines a safe path to deploy and recover the Finance Analyzer stack.

## Scope

- Frontend deployment (TanStack Start app in `frontend/`)
- Backend deployment (FastAPI app in `src/finance_analyzer/api/`)
- Database schema changes (Drizzle migration flow in `frontend/db/`)

## Release Checklist

1. Ensure CI is green on the release commit:
   - frontend lint, build, unit tests
   - backend syntax check and tests
   - E2E smoke test
2. Verify database migration generation is clean:
   - `cd frontend`
   - `npm run db:generate`
3. Verify local backend tests:
   - `cd ..`
   - `uv run pytest`
4. Capture release metadata:
   - git SHA
   - migration IDs included
   - environment variables changed

## Deployment Procedure

1. Deploy backend application first.
2. Run database migrations against target database:
   - `cd frontend`
   - `npm run db:migrate`
3. Deploy frontend application.
4. Run post-deploy smoke checks:
   - `GET /` on backend returns 200
   - `GET /ops/metrics` returns 200 and includes counters
   - Open frontend `/about` route and verify page load

## Post-Deploy Verification

1. Confirm request logs include `request_id` and status fields.
2. Confirm RPC responses include `x-request-id` header.
3. Confirm no spike in 5xx status counts on `/ops/metrics`.
4. Confirm critical flows (upload -> analysis pages) are accessible.

## Rollback Triggers

Rollback immediately if any of the following occur:

1. Sustained 5xx errors after deploy.
2. Migration failures causing application unavailability.
3. Auth/tenant access regressions (403/401 on known-good users).
4. E2E smoke checks fail in production.

## Rollback Procedure

1. Frontend rollback:
   - Revert to previous stable frontend artifact/release.
2. Backend rollback:
   - Revert to previous stable backend artifact/release.
3. Database rollback strategy:
   - If migration is backward-compatible: keep schema and roll back app only.
   - If migration is breaking: restore from pre-deploy backup/snapshot and redeploy previous app version.
4. Re-run smoke checks on rolled back version:
   - `GET /`
   - `GET /ops/metrics`
   - frontend `/about` route

## Incident Notes Template

Record the following for each rollback:

1. Timestamp and release SHA.
2. Trigger and observed symptoms.
3. Mitigation steps taken.
4. Final recovery state.
5. Follow-up action items.
