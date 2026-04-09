# Engineering Hardening Checklist (30/60/90)

This checklist turns the project analysis into executable sprint work.

Use this format for each task:
- **Owner**: Backend / Frontend / Platform / Security / QA
- **Effort**: S (1-2 days), M (3-5 days), L (1-2 weeks)
- **Done when**: measurable acceptance criteria

## Priority Guide

- **P0**: Must do before broad production rollout
- **P1**: Should do in the next release cycle
- **P2**: Maturity and scale improvements

---

## P0 Tasks (Start Immediately)

### 1) Enforce job-level authorization policy
- **Owner**: Backend
- **Effort**: L
- **Files**:
  - `backend/app/api/jobs.py`
  - `backend/app/api/workflow.py`
  - `backend/app/api/candidates.py`
  - `backend/app/api/analytics.py`
  - `backend/app/core/auth.py`
  - `backend/tests/api/`
- **Action**:
  - Add centralized read/write job policy helpers.
  - Apply policy checks on all endpoints that access `job_id`.
  - Add negative tests: user A cannot read/modify user B job.
- **Done when**:
  - All protected routes enforce scope policy.
  - New API tests pass for cross-user access denial.

### 2) Make orchestration execution durable and idempotent
- **Owner**: Backend + Platform
- **Effort**: L
- **Files**:
  - `backend/app/core/orchestrator.py`
  - `backend/app/api/jobs.py`
  - `backend/app/api/workflow.py`
  - `backend/app/models/db_models.py`
  - `backend/tests/integration/`
- **Action**:
  - Prevent concurrent duplicate runs per job (lock/idempotency key).
  - Ensure workflow can recover safely after process restart.
  - Record run metadata (`started_at`, `finished_at`, `status`, `last_error`).
- **Done when**:
  - Duplicate trigger requests do not fork conflicting runs.
  - Integration tests validate restart-safe behavior.

### 3) Restrict raw workflow state mutation endpoint
- **Owner**: Backend + Security
- **Effort**: M
- **Files**:
  - `backend/app/api/workflow.py`
  - `backend/app/models/state.py`
  - `backend/tests/api/`
- **Action**:
  - Replace unrestricted patching with allowlisted fields.
  - Restrict endpoint to admin-only and/or non-production environments.
  - Log every state mutation with actor and reason.
- **Done when**:
  - Unallowlisted fields are rejected with clear errors.
  - Audit logs include actor, timestamp, changed keys, and reason.

### 4) Make high/critical security findings blocking
- **Owner**: Platform + Security
- **Effort**: S
- **Files**:
  - `.github/workflows/ci.yml`
- **Action**:
  - Convert high/critical dependency findings from informational to blocking for protected branches.
  - Keep medium/low informational initially to avoid release friction.
- **Done when**:
  - CI fails on high/critical findings.
  - Branch protection references the correct required checks.

---

## P1 Tasks (Next Release Cycle)

### 5) Add CSRF defenses for cookie-auth mutation routes
- **Owner**: Backend + Frontend
- **Effort**: M
- **Files**:
  - `backend/app/main.py`
  - `backend/app/api/auth.py`
  - `backend/app/api/workflow.py`
  - `frontend/src/lib/api.ts`
  - `frontend/src/hooks/useAuth.tsx`
  - `backend/tests/api/`
- **Action**:
  - Implement CSRF token strategy (double-submit or equivalent).
  - Validate token/origin on state-changing endpoints.
  - Update frontend to send required CSRF token header.
- **Done when**:
  - Mutation routes reject missing/invalid CSRF tokens.
  - Authenticated UI flows continue to work in E2E tests.

### 6) Introduce DB migration framework
- **Owner**: Backend + Platform
- **Effort**: M
- **Files**:
  - `backend/app/core/database.py`
  - `backend/` (migration config and versions)
  - `.github/workflows/ci.yml`
  - `scripts/verify-backend.*`
- **Action**:
  - Add migration tooling and baseline migration.
  - Replace implicit schema drift with explicit migration runs.
  - Run migration checks in CI.
- **Done when**:
  - New environments are built from migrations, not `create_all`.
  - CI validates migration up/down or head consistency.

### 7) Harden upload limits and validation
- **Owner**: Backend + Security
- **Effort**: M
- **Files**:
  - `backend/app/api/jobs.py`
  - `backend/app/rag/parser.py`
  - `backend/app/config.py`
  - `backend/tests/api/`
- **Action**:
  - Enforce max file size and strict MIME checks.
  - Add parser timeout and graceful error handling.
  - Reject suspicious payloads early.
- **Done when**:
  - Oversized/invalid files are blocked predictably.
  - Tests cover normal and malicious upload cases.

### 8) Add server-side route protection in frontend
- **Owner**: Frontend
- **Effort**: M
- **Files**:
  - `frontend/src/app/`
  - `frontend/src/hooks/useAuth.tsx`
  - `frontend/src/lib/api.ts`
  - `frontend/e2e/`
- **Action**:
  - Add route guard enforcement before protected UI renders.
  - Reduce auth flicker and repeated session checks.
- **Done when**:
  - Unauthenticated users are redirected before protected pages paint.
  - Auth flow tests cover direct URL access to protected routes.

---

## P2 Tasks (Scale and Maturity)

### 9) Standardize frontend data fetching and cache behavior
- **Owner**: Frontend
- **Effort**: L
- **Files**:
  - `frontend/src/app/dashboard/`
  - `frontend/src/app/jobs/page.tsx`
  - `frontend/src/app/approvals/page.tsx`
  - `frontend/src/store/useJobStore.ts`
- **Action**:
  - Adopt a single cache/refetch strategy.
  - Remove duplicate request patterns and stale data edge cases.
- **Done when**:
  - Key pages share consistent refetch and stale policies.
  - User actions reflect in UI without manual refresh.

### 10) Expand test coverage for auth/store/websocket behavior
- **Owner**: Frontend + QA
- **Effort**: M
- **Files**:
  - `frontend/src/hooks/useAuth.tsx`
  - `frontend/src/hooks/useWebSocket.ts`
  - `frontend/src/store/useJobStore.ts`
  - `frontend/__tests__/`
  - `frontend/e2e/`
- **Action**:
  - Add focused unit/integration tests for session lifecycle, reconnect logic, and state transitions.
- **Done when**:
  - Regression tests exist for auth redirect, socket reconnect, and store mutation flows.

### 11) Strengthen observability and on-call readiness
- **Owner**: Platform + Backend
- **Effort**: M
- **Files**:
  - `backend/app/api/analytics.py`
  - `docs/ARCHITECTURE.md`
  - `docs/RELEASE_CHECKLIST.md`
  - `docs/` (new runbook docs)
- **Action**:
  - Define alertable metrics and operational thresholds.
  - Add runbook for incident triage and rollback decisions.
- **Done when**:
  - Team can diagnose queue/workflow/auth failures using documented steps.

### 12) Add governance docs and ownership metadata
- **Owner**: Platform
- **Effort**: S
- **Files**:
  - `SECURITY.md` (new)
  - `CONTRIBUTING.md` (new)
  - `CODEOWNERS` (new)
- **Action**:
  - Document vulnerability reporting, contribution workflow, and file ownership.
- **Done when**:
  - PR routing and security reporting are clearly defined and visible.

---

## 30/60/90-Day Execution Plan

### First 30 days
- Complete tasks 1-4 (all P0).
- Target outcome: safer authorization, safer state mutation, stronger CI gate.

### Day 31-60
- Complete tasks 5-8 (P1).
- Target outcome: better auth hardening, migration discipline, safer upload path.

### Day 61-90
- Complete tasks 9-12 (P2).
- Target outcome: improved maintainability, test depth, and operational maturity.

---

## Weekly Tracking Template

Use this in sprint reviews:

- **Done this week**:
- **In progress**:
- **Blocked**:
- **Risk raised**:
- **Decision needed**:
- **Next week focus**:
