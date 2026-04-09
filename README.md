# PRO HR â€” Autonomous Multi-Agent Recruitment Ecosystem

A multi-agent recruitment platform with a **deterministic Python orchestrator** (LangChain / OpenAI for LLM steps), **human-in-the-loop gates**, and **FAISS-backed RAG** for resume search.

## ðŸ—ï¸ Architecture

```
Frontend (Next.js 16)  â†’  FastAPI Backend  â†’  Orchestrator (state machine)
                                                    â†“
                                            5 pipeline agents (see below)
                                                    â†“
                                    FAISS vector index (LangChain) + SQLite/Postgres
```

The runtime workflow is **not** LangGraph-driven: `backend/app/core/orchestrator.py` advances stages and invokes agent nodes until a HITL breakpoint or completion. **LangGraph** is optional for local experiments (`backend/requirements-dev.txt`, e.g. `test_graph_standalone.py`).

**Deeper technical map:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

**Roadmap:** [docs/HIGH_VALUE_ROADMAP.md](docs/HIGH_VALUE_ROADMAP.md) (Phases **Aâ€“C** done). **Changes:** [CHANGELOG.md](CHANGELOG.md).

### Pipeline agents (wired in the orchestrator)

| # | Agent | Role |
|---|-------|------|
| 1 | **JD Architect** | Drafts bias-aware job descriptions |
| 2 | **The Liaison** | Human-in-the-loop approval gatekeeper (JD, shortlist, hire) |
| 3 | **The Scout** | Semantic resume search over the FAISS index (RAG) |
| 4 | **The Screener** | Gap analysis and scoring |
| 5 | **The Coordinator** | Post-shortlist automation: scheduling, interview assessment (LLM), deterministic hire decision, offer drafting |

Additional modules (`outreach`, `response_tracker`, standalone `offer_generator`) exist in the repo but are **not** part of the default orchestration path above.

## ðŸš€ Quick Start

### Prerequisites

- **Python 3.11.x** (matches CI and `backend/Dockerfile`; use `.python-version` with pyenv). Other versions are not validated in CI.
- **Node.js 20+** (matches CI; LTS recommended)
- OpenAI API Key

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env: SECRET_KEY (32+ chars), OPENAI_API_KEY, and optionally FRONTEND_URL / CORS
uvicorn app.main:app --reload
```

Optional LangGraph experiments: `pip install -r requirements-dev.txt` (not required for the API or CI).

Quick tests (from `backend/`, set `SECRET_KEY` as in CI): `pytest -m "unit or api" -q` for a fast slice; **`pytest tests -q`** matches the backend CI job. CI also runs an **informational** full-app `mypy` report (`mypy-full.ini`) that does not fail the pipeline â€” use it to track typing debt.

Backend runs at **<http://localhost:8000>** (API docs: `/docs`)

### Frontend Setup

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Dashboard runs at **<http://localhost:3000>**

### Environment variables

| Area | Variable | Notes |
|------|----------|--------|
| Backend | `SECRET_KEY` | **Required.** 32+ character random string for JWT signing. |
| Backend | `OPENAI_API_KEY` | Required for agents and embeddings. |
| Backend | `LLM_MODEL` / `EMBEDDING_MODEL` | Optional overrides (defaults in `app/config.py`). |
| Backend | `FRONTEND_URL` | Origin of the Next app; included in CORS allow list. |
| Backend | `CORS_EXTRA_ORIGINS` | Optional comma-separated origins (e.g. staging). |
| Backend | `AUTH_COOKIE_SECURE` / `AUTH_COOKIE_SAMESITE` | Use `secure=true` and appropriate `samesite` in production over HTTPS. |
| Backend | `WS_TICKET_EXPIRE_MINUTES` | Lifetime for WS tickets used in `/ws/{job_id}?token=...`. |
| Backend | `WS_ALLOW_LEGACY_BROWSER_TOKEN` | Legacy fallback for full JWT in WS token. Default is **false**; keep false in production. |
| Backend | `SEED_DEMO_USERS` | Dev only (`development`/`dev`/`local`); set `true` plus `DEMO_*_PASSWORD` to seed demo accounts. |
| Frontend | `NEXT_PUBLIC_API_URL` | If empty, Axios uses same-origin `/api` (Next rewrites). If set, browser calls this origin (must be CORS-allowed). |
| Frontend | `BACKEND_URL` | Next **server** rewrite target (local dev: `http://127.0.0.1:8000`; Docker build: `http://backend:8000`). |
| Frontend | `NEXT_PUBLIC_WS_URL` | WebSocket URL for live updates (often `ws://localhost:8000` when the API publishes port 8000). |
| CI | `SECRET_KEY` | GitHub Actions sets this for `pytest`; copy the pattern for local test runs if needed. |

**CI:** Backend runs **pytest** in three steps (`tests/unit` + `tests/api`, then `tests/integration`, then `tests/e2e`). Frontend runs **lint**, **Jest**, **build**, and **Playwright** (`npm run test:e2e`). Manual HTTP scripts (`backend/e2e_*.py`) are **not** in CI; see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#testing).

### Observability endpoints

- **`GET /api/health`** — includes in-memory observability counters under `observability`.
- **`GET /api/analytics/observability`** — JSON counters, **admin-only**.
- **`GET /api/analytics/metrics`** — Prometheus-style plaintext counters, **admin-only**.
- Request tracing: backend adds **`x-request-id`** to responses and logs request completion with duration.

### WS migration checklist

- Set `WS_ALLOW_LEGACY_BROWSER_TOKEN=false` in staging and production.
- Verify: login -> open a job page -> live updates stream over WS.
- Keep rollback path documented: temporarily set `WS_ALLOW_LEGACY_BROWSER_TOKEN=true` only if an older client must be supported.

### Resume uploads (API)

The dashboard uses **`POST /api/jobs/{job_id}/resumes`** (PDF only, sourcing/screening). **`POST /api/resumes/upload`** is **deprecated** for product use (still available for scripts; see `Deprecation` / `Sunset` headers and [CHANGELOG.md](CHANGELOG.md)). Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#resume-indexing-two-post-routes).

### Docker Compose

Prerequisites: **`backend/.env`** with at least **`SECRET_KEY`**, **`OPENAI_API_KEY`**, and **`FRONTEND_URL=http://localhost:3000`** (matches the URL users open; required for CORS and sensible cookie behavior).

**Default (recommended)** - same-origin API via Next rewrites:

```bash
docker compose up --build
```

Open **http://localhost:3000**. The UI calls **`/api/...`** on port 3000; Next proxies to the **`backend`** service. WebSockets still use **`ws://localhost:8000`** from the browser to the published API port.

**Alternate** - browser talks directly to port 8000 for REST:

```bash
docker compose -f docker-compose.yml -f docker-compose.direct-api.yml up --build
```

Details, env inventory, and production patterns: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#environment--deployment-inventory-phase-a).

## ðŸ“± Dashboard Pages

- **Dashboard** â€” Overview metrics, active pipelines, agent roster
- **Jobs** â€” Create job requisitions, view generated JDs
- **Candidates** â€” Scored candidate cards with gap analysis
- **Approvals** â€” HITL gates for JD, shortlist, and hire decisions
- **Interviews** â€” Scheduled interviews and competency assessments
- **Decisions** â€” Final hire/no-hire with explainable reasoning
- **Audit Trail** â€” Timeline of all agent actions and decisions

## ðŸ”‘ Key Features

- **Bias Mitigation** â€” Guardrails in agent prompts and audit emphasis
- **Explainable Scoring** â€” Structured match reasoning and competency gaps
- **HITL Gates** â€” Three human approval checkpoints in the pipeline
- **RAG Search** â€” FAISS + embeddings for semantic resume retrieval (see `backend/app/rag/embeddings.py`)
- **Audit Trail** â€” Decision history with agent attribution

## ðŸ› ï¸ Tech Stack

- **Orchestration**: Custom Python orchestrator (`app/core/orchestrator.py`) with staged pipeline
- **LLM**: OpenAI (default model from settings, e.g. `gpt-4o`)
- **Backend**: FastAPI + Python 3.11
- **Vector search**: FAISS via LangChain (`langchain_community.vectorstores.FAISS`)
- **Frontend**: Next.js 16 + TypeScript + Tailwind CSS
- **Real-time**: WebSocket for live pipeline updates


## ðŸš¢ Release Process

Before tagging/deploying, run the checklist in [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).

- Required: green backend + frontend CI jobs.
- Informational: mypy-full-report, backend-security-audit, frontend-security-audit (non-blocking trend checks).
- Always include rollback notes for auth/deploy flags (for example WS_ALLOW_LEGACY_BROWSER_TOKEN).

## Project Closeout (Stability)

Use this as the final runbook before handoff.

### 1) Runtime stability checks (local)

From repo root:

```bash
bash scripts/verify-all.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-all.ps1
```

Expected outcome:
- Backend lint/type/tests pass.
- Frontend lint/tests/build pass.
- Playwright smoke/full-stack flows pass.

### 2) Pipeline health checks (manual)

- Login as an HR user and create one pipeline.
- Verify stage movement:
  - `jd_review` -> `shortlist_review` -> `interviewing` -> `hire_review` -> `completed`
- Confirm HITL gates at JD/shortlist/hire work as expected.
- Confirm Kanban card click opens `Audit Trail` for that pipeline.
- Confirm approved/completed pipelines no longer appear in pending approvals.

### 3) Security and environment hardening

- Keep `WS_ALLOW_LEGACY_BROWSER_TOKEN=false` outside emergency rollback windows.
- Use a strong `SECRET_KEY` (32+ chars) and set `AUTH_COOKIE_SECURE=true` for HTTPS deployments.
- Keep `.env`, local DB files, and generated auth state out of git (`.gitignore` already covers these).
- Rotate shared API credentials before production handoff.

### 4) CI/CD completion criteria

- `secret-scan`, `backend`, and `frontend` jobs must be green.
- Optional audit jobs (`mypy-full-report`, dependency audits) should be reviewed and tracked.
- Merge only from a passing commit SHA.

### 5) Ongoing maintenance cadence

- Weekly: review dependency and security audit reports.
- Per feature: add/adjust backend tests and Playwright coverage.
- Per release: update `CHANGELOG.md` and rerun `scripts/verify-all.*`.
- Monthly: validate live walkthrough path (create -> invite -> select -> offer -> completed).

