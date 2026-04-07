# PRO HR — Autonomous Multi-Agent Recruitment Ecosystem

A multi-agent recruitment platform with a **deterministic Python orchestrator** (LangChain / OpenAI for LLM steps), **human-in-the-loop gates**, and **FAISS-backed RAG** for resume search.

## 🏗️ Architecture

```
Frontend (Next.js 16)  →  FastAPI Backend  →  Orchestrator (state machine)
                                                    ↓
                                            5 pipeline agents (see below)
                                                    ↓
                                    FAISS vector index (LangChain) + SQLite/Postgres
```

The runtime workflow is **not** LangGraph-driven: `backend/app/core/orchestrator.py` advances stages and invokes agent nodes until a HITL breakpoint or completion. **LangGraph** is optional for local experiments (`backend/requirements-dev.txt`, e.g. `test_graph_standalone.py`).

**Deeper technical map:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

**Roadmap:** [docs/HIGH_VALUE_ROADMAP.md](docs/HIGH_VALUE_ROADMAP.md) (Phases **A–C** done). **Changes:** [CHANGELOG.md](CHANGELOG.md).

### Pipeline agents (wired in the orchestrator)

| # | Agent | Role |
|---|-------|------|
| 1 | **JD Architect** | Drafts bias-aware job descriptions |
| 2 | **The Liaison** | Human-in-the-loop approval gatekeeper (JD, shortlist, hire) |
| 3 | **The Scout** | Semantic resume search over the FAISS index (RAG) |
| 4 | **The Screener** | Gap analysis and scoring |
| 5 | **The Coordinator** | Post-shortlist automation: scheduling, interview assessment (LLM), deterministic hire decision, offer drafting |

Additional modules (`outreach`, `response_tracker`, standalone `offer_generator`) exist in the repo but are **not** part of the default orchestration path above.

## 🚀 Quick Start

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

Quick tests (from `backend/`, set `SECRET_KEY` as in CI): `pytest -m "unit or api" -q` for a fast slice; **`pytest tests -q`** matches the backend CI job. CI also runs an **informational** full-app `mypy` report (`mypy-full.ini`) that does not fail the pipeline — use it to track typing debt.

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
| Backend | `SEED_DEMO_USERS` | Dev only (`development`/`dev`/`local`); set `true` plus `DEMO_*_PASSWORD` to seed demo accounts. |
| Frontend | `NEXT_PUBLIC_API_URL` | If empty, Axios uses same-origin `/api` (Next rewrites). If set, browser calls this origin (must be CORS-allowed). |
| Frontend | `BACKEND_URL` | Next **server** rewrite target (local dev: `http://127.0.0.1:8000`; Docker build: `http://backend:8000`). |
| Frontend | `NEXT_PUBLIC_WS_URL` | WebSocket URL for live updates (often `ws://localhost:8000` when the API publishes port 8000). |
| CI | `SECRET_KEY` | GitHub Actions sets this for `pytest`; copy the pattern for local test runs if needed. |

**CI:** Backend runs **pytest** in three steps (`tests/unit` + `tests/api`, then `tests/integration`, then `tests/e2e`). Frontend runs **lint**, **Jest**, **build**, and **Playwright** (`npm run test:e2e`). Manual HTTP scripts (`backend/e2e_*.py`) are **not** in CI; see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#testing).

### Resume uploads (API)

The dashboard uses **`POST /api/jobs/{job_id}/resumes`** (PDF only, sourcing/screening). **`POST /api/resumes/upload`** is **deprecated** for product use (still available for scripts; see `Deprecation` / `Sunset` headers and [CHANGELOG.md](CHANGELOG.md)). Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#resume-indexing-two-post-routes).

### Docker Compose

Prerequisites: **`backend/.env`** with at least **`SECRET_KEY`**, **`OPENAI_API_KEY`**, and **`FRONTEND_URL=http://localhost:3000`** (matches the URL users open; required for CORS and sensible cookie behavior).

**Default (recommended)** — same-origin API via Next rewrites:

```bash
docker compose up --build
```

Open **http://localhost:3000**. The UI calls **`/api/...`** on port 3000; Next proxies to the **`backend`** service. WebSockets still use **`ws://localhost:8000`** from the browser to the published API port.

**Alternate** — browser talks directly to port 8000 for REST:

```bash
docker compose -f docker-compose.yml -f docker-compose.direct-api.yml up --build
```

Details, env inventory, and production patterns: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#environment--deployment-inventory-phase-a).

## 📱 Dashboard Pages

- **Dashboard** — Overview metrics, active pipelines, agent roster
- **Jobs** — Create job requisitions, view generated JDs
- **Candidates** — Scored candidate cards with gap analysis
- **Approvals** — HITL gates for JD, shortlist, and hire decisions
- **Interviews** — Scheduled interviews and competency assessments
- **Decisions** — Final hire/no-hire with explainable reasoning
- **Audit Trail** — Timeline of all agent actions and decisions

## 🔑 Key Features

- **Bias Mitigation** — Guardrails in agent prompts and audit emphasis
- **Explainable Scoring** — Structured match reasoning and competency gaps
- **HITL Gates** — Three human approval checkpoints in the pipeline
- **RAG Search** — FAISS + embeddings for semantic resume retrieval (see `backend/app/rag/embeddings.py`)
- **Audit Trail** — Decision history with agent attribution

## 🛠️ Tech Stack

- **Orchestration**: Custom Python orchestrator (`app/core/orchestrator.py`) with staged pipeline
- **LLM**: OpenAI (default model from settings, e.g. `gpt-4o`)
- **Backend**: FastAPI + Python 3.11
- **Vector search**: FAISS via LangChain (`langchain_community.vectorstores.FAISS`)
- **Frontend**: Next.js 16 + TypeScript + Tailwind CSS
- **Real-time**: WebSocket for live pipeline updates
