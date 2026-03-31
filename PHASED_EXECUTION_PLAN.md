# Finance Analyzer - Phased Execution Plan

This plan turns the project into a production-grade personal finance platform with persistent data, strong API contracts, and feature-complete workflows.

## Phase 1 - Foundation Stabilization (Completed)

Goal: Stabilize API integration and remove demo contract leftovers.

### Scope

- Replace demo ORPC/OpenAPI schema references with finance schemas.
- Standardize ORPC procedure request handling and error propagation.
- Fix endpoint path mismatches in ORPC procedures.
- Add missing procedure contracts needed by dashboard workflows.

### Delivered in this phase

- ORPC schema moved from Todo to finance contracts.
- OpenAPI route updated to publish finance entities.
- Finance procedures now use:
  - consistent API base URL fallback
  - unified JSON/error handling
  - corrected forecast endpoint path
  - transactions procedure support

### Exit criteria

- Frontend build and type checks pass.
- ORPC finance routes return correct payload schemas.
- OpenAPI docs no longer contain Todo demo schema.

## Phase 2 - Neon + Drizzle Data Model (Completed)

Goal: Establish persistent finance domain schema in Postgres.

### Scope

- Replace todo schema with finance entities.
- Add indexes, constraints, and dedupe keys.
- Add migration strategy and seed scaffolding.

### Planned tables

- users
- households
- household_members
- accounts
- statement_uploads
- transactions
- categories
- category_rules
- transaction_enrichments
- budgets
- budget_allocations
- recurring_transactions
- goals
- forecasts
- forecast_points
- alerts
- audit_events

### Exit criteria

- Drizzle schema compiles.
- Migration SQL generated and reviewed.
- Local apply/migrate flow works against Neon.

### Delivered in this phase

- Replaced demo todo schema with full finance domain Drizzle schema.
- Added dedicated Neon + Drizzle client setup for server-side usage.
- Generated Drizzle migration SQL from schema.
- Replaced SQL bootstrap from todo demo to finance tables and enums.

## Phase 3 - Persistent Ingestion + Analytics Storage (Completed)

Goal: Remove in-memory processing dependency from backend lifecycle.

### Scope

- Persist uploads, normalized transactions, enrichment artifacts.
- Add idempotent ingest pipeline with file hash tracking.
- Save anomalies and forecast outputs per run.

### Exit criteria

- Restart-safe analytics data.
- Upload history + status available.
- Duplicate upload behavior deterministic.

### Delivered so far

- Added ORPC procedure to sync processed FastAPI transactions into Neon tables.
- Added demo household/account bootstrapping for single-user persistence flows.
- Added import history and persisted transaction read procedures.
- Wired dashboard upload flow to trigger persistence sync and DB cache invalidation.
- Added backend cache persistence for processed analytics data with lazy reload from disk to keep analysis/forecast endpoints restart-safe.

## Phase 4 - Product Pages + Usability Expansion (Completed)

Goal: Make application usable as a daily finance workspace.

### Scope

- Add pages:
  - Transactions
  - Imports
  - Categories and Rules
  - Budgets
  - Goals
  - Recurring
  - Alerts
- Add filters, edits, bulk actions, and export tools.

### Exit criteria

- End-to-end user journey from upload to actionable decisions.
- Mobile-responsive workflows across all primary pages.

### Delivered so far

- Added Imports page with manual sync trigger and import history table.
- Added Persisted Transactions page with search, direction filtering, and anomaly flags.
- Added Categories and Rules page with persisted category summaries, rule CRUD actions, and rule preview matching.
- Added Budgets page with budget creation, active-state toggling, and allocation management with spend tracking.
- Added Goals page with target tracking, status filtering, and inline progress updates.
- Added Recurring page with cadence tracking, due-date management, and inline pattern updates.
- Added Alerts page with severity/type filters, read-state edits, bulk mark-as-read, and CSV export.
- Added budget overview and allocation CRUD procedures in ORPC for persisted workflows.
- Added goals overview and goal CRUD procedures in ORPC for persisted workflows.
- Added recurring overview and recurring CRUD procedures in ORPC for persisted workflows.
- Added alerts overview and alert state/cleanup procedures in ORPC for persisted workflows.
- Updated header navigation for Dashboard, Imports, Transactions, Categories, Budgets, Goals, Recurring, Alerts, and About.

## Phase 5 - Security, Quality, and Operations

Goal: Production readiness.

### Scope

- Add auth and tenant isolation with role model.
- Add tests:
  - unit
  - integration
  - end-to-end
- Add observability:
  - structured logs
  - request IDs
  - failure metrics
- Add CI gates for lint/type/build/tests/migrations.

### Exit criteria

- CI green and enforceable.
- Core user flows covered by tests.
- Deployment and rollback playbook documented.

## Working method

1. Complete one phase to defined exit criteria.
2. Validate with build/tests after every milestone.
3. Commit phase changes with clear migration notes.
4. Start next phase only after acceptance of previous one.
