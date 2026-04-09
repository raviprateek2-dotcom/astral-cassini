# Incident Response Runbook

Use this runbook for production incidents affecting auth, workflows, or live updates.

## Severity Levels

- **SEV-1**: Full outage or data corruption risk.
- **SEV-2**: Core workflow partially degraded, no confirmed data loss.
- **SEV-3**: Non-critical degradation or one-off failure.

## First 10 Minutes

1. Confirm incident scope (who is impacted, which feature, when started).
2. Capture request IDs (`x-request-id`) from failing client/API responses.
3. Check `/api/health` for backend availability and observability counters.
4. Check CI/deploy history for recent changes.
5. Assign incident commander and one scribe.

## Fast Diagnostics

### Auth failures (401/403 spikes)

- Validate auth cookie settings:
  - `AUTH_COOKIE_SECURE`
  - `AUTH_COOKIE_SAMESITE`
- Confirm CSRF behavior for browser mutation calls:
  - `csrf_token` cookie exists
  - `x-csrf-token` header is sent and matches
- Verify role and ownership checks for affected `job_id`.

### Workflow stalled / duplicate behavior

- Query affected job state:
  - `GET /api/jobs/{job_id}`
  - `GET /api/workflow/{job_id}/status`
- Inspect workflow metadata in state:
  - `state._orchestrator.status`
  - `started_at`, `finished_at`, `last_error`
- Validate no repeated orchestration trigger loops in logs.

### WebSocket/live updates missing

- Confirm ticket minting:
  - `GET /api/auth/ws-ticket?job_id=...`
- Verify WS counters:
  - `ws_ticket_issued`
  - `ws_ticket_denied`
  - `ws_connect_success`
  - `ws_connect_rejected`
- Validate `NEXT_PUBLIC_WS_URL` points to reachable backend WS endpoint.

## Containment Actions

- Roll back to last known good commit/tag if root cause is recent deploy.
- If browser auth path is unstable, temporarily limit high-risk mutations while preserving read APIs.
- Disable unsafe manual state interventions unless incident commander approves admin override.

## Recovery Validation Checklist

- Login/logout works across browsers.
- One fresh job pipeline reaches `completed` through approvals.
- Resume upload and screening succeed.
- WebSocket updates stream on active job page.
- Admin observability endpoints return expected counters.

## Post-Incident Requirements

- Write incident summary within 24h:
  - impact, root cause, timeline, mitigations, follow-up tasks
- Add regression tests for the exact failure mode.
- Update this runbook and `docs/RELEASE_CHECKLIST.md` if process gaps were found.
