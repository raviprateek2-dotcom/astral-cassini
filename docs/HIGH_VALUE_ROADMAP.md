# High-value completion roadmap

This plan finishes the items called out as **highest remaining impact** after doc truthfulness, CI, and test markers. Order balances **risk**, **dependencies**, and **user-visible payoff**.

---

## Phase A — Deploy and operations ✅ (implemented)

**Goal:** Anyone can run the stack in Docker (or staging) without guessing origins or breaking the browser.

| Step | Task | Status |
|------|------|--------|
| A1 | **Inventory** — `NEXT_PUBLIC_*`, `BACKEND_URL`, cookies | [ARCHITECTURE.md — Environment & deployment inventory](ARCHITECTURE.md#environment--deployment-inventory-phase-a) |
| A2 | **Compose variants** | Default `docker-compose.yml` (same-origin `/api`, `BACKEND_URL=http://backend:8000`); `docker-compose.direct-api.yml` override; README commands |
| A3 | **Production pattern** | [ARCHITECTURE.md — Deployment topologies](ARCHITECTURE.md#deployment-topologies) (reverse proxy first) |
| A4 | **Health-gated startup** | `depends_on: service_healthy`; backend image includes **curl**; healthcheck tuned |

**Dependencies:** None technical beyond current repo.  
**Risks:** Over-engineering multi-compose files — keep **two** variants max until you have real staging URLs.

---

## Phase B — Config and API clarity ✅ (implemented)

**Goal:** Remove dead configuration and reduce duplicate upload semantics.

| Step | Task | Status |
|------|------|--------|
| B1 | Remove **`chroma_persist_dir`** from Settings | **Done:** [CHANGELOG.md](../CHANGELOG.md); field removed from `app/config.py` |
| B2 | Deprecate **`POST /api/resumes/upload`** | **Done:** `deprecated=True` in FastAPI; `Deprecation` + `Sunset` + `Link` headers; ARCHITECTURE table updated |
| B3 | OpenAPI `servers` in staging | Skipped (optional) |

**Dependencies:** Phase A helps B2 if you align “admin bulk index” with an internal route behind role `admin` only.

---

## Phase C — WebSocket authentication hardening ✅ (implemented)

**Goal:** Reduce impact of XSS on **long-lived session equivalence** over WebSockets.

**Shipped:** Short-lived signed JWT **WS tickets** (`aud=prohr-ws`, bound to `job_id`) via **`GET /api/auth/ws-ticket?job_id=`** (cookie session). `connectWebSocket` fetches a ticket before connect/reconnect. Optional legacy fallback: full access token in `?token=` while **`WS_ALLOW_LEGACY_BROWSER_TOKEN=true`** (default).

| Step | Task | Status |
|------|------|--------|
| C1 | Threat model + cookie `HttpOnly` for REST | **Done:** `ARCHITECTURE.md` WebSocket auth note |
| C2 | Issue WS ticket (stateless JWT, `job_id` binding) | **Done:** `GET /api/auth/ws-ticket`, `ws_ticket_expire_minutes` |
| C3 | Frontend ticket flow; no `sessionStorage` WS copy | **Done:** `api.getWsTicket` + async `connectWebSocket` |
| C4 | WS handler validates `aud` + permissions | **Done:** `app/api/websocket.py`; API tests for ticket route |
| C5 | Rollout / fallback flag | **Done:** `ws_allow_legacy_browser_token` in `Settings` |

**Dependencies:** Phase A (stable origins) simplifies cookie + ticket issuance.  
**Risks:** Reconnect storms — each reconnect calls **`/api/auth/ws-ticket`** for a fresh ticket (acceptable for MVP).

---

## Suggested sequence

1. **Phase A** (deploy truth) — unblocks confident testing of Phases B and C.  
2. **Phase B** (config + upload clarity) — quick wins, low regression risk.  
3. **Phase C** (WS hardening) — largest change; needs design call on ticket storage (stateless signed JWT vs Redis).

---

## Out of scope for this roadmap (track separately)

- Replacing FAISS with managed vector DB in production.  
- Full pen test / SOC2.  
- Mobile or third-party SSO (OIDC) — would alter Phase C ticket issuance.

---

## Tracking

Check off phases in PR descriptions (e.g. “Closes Phase A2–A3”). Update this file when scope or decisions change.
