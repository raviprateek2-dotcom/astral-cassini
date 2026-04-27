# PRO HR - Autonomous Multi-Agent Recruitment Ecosystem

PRO HR is a full-stack recruitment platform with:

- **Frontend:** Next.js 16 (`frontend/`)
- **Backend:** FastAPI + Python 3.11 (`backend/`)
- **Core workflow:** deterministic orchestration, FAISS-backed resume retrieval, approvals, and audit trail

This guide is optimized for people who download the repository ZIP and want it running locally quickly and reliably.

## Run From Downloaded ZIP (No Git Required)

### 1) Extract and open terminal

1. Download ZIP from GitHub.
2. Extract it.
3. Open terminal in the extracted folder (repo root, where this file is).

### 2) Install prerequisites

- Python **3.11**
- Node.js **20+** (Node 22 works)
- npm

### 3) Bootstrap once

#### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-local.ps1
```

#### macOS/Linux

```bash
bash scripts/bootstrap-local.sh
```

The bootstrap scripts:

- create `backend/.env` from `backend/.env.example` if missing
- create `frontend/.env.local` from `frontend/.env.example` if missing
- install backend dependencies
- install frontend dependencies

### 4) Start app (two terminals)

#### Terminal A - backend

```powershell
cd backend
py -3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If `py -3.11` is unavailable, use `python -m uvicorn ...` with Python 3.11.

#### Terminal B - frontend

```powershell
cd frontend
npm run dev -- -p 3000
```

### 5) Open in browser

- App: `http://localhost:3000`
- API docs: `http://127.0.0.1:8000/docs`

## Authentication Behavior (Local)

### Open access by default

The backend template enables:

```env
AUTH_DISABLED=true
```

This means API routes are accessible locally without login/password checks.

### Re-enable strict auth later

Set in `backend/.env`:

```env
AUTH_DISABLED=false
```

Then restart backend.

## Quick End-to-End Walkthrough

1. Open `http://localhost:3000`.
2. Click **Launch Control Center**.
3. Go to **Jobs**, create a job.
4. Upload resumes.
5. Check **Approvals**, **Decisions**, and **Audit** pages.

Expected: pipeline data appears and pages are accessible without auth blockers in local open-access mode.

## Verification Commands

### Full project verification

#### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-all.ps1
```

#### macOS/Linux

```bash
bash scripts/verify-all.sh
```

### Individual checks

- Backend: `bash scripts/verify-backend.sh` or `.\scripts\verify-backend.ps1`
- Frontend: `bash scripts/verify-frontend.sh` or `.\scripts\verify-frontend.ps1`

## Docker Compose (Alternative Local Run)

From repo root:

```bash
docker compose up --build
```

Then open:

- `http://localhost:3000`
- `http://127.0.0.1:8000/docs`

If Docker fails with engine/pipe errors, start Docker Desktop first.

## Project Structure

- `backend/` - FastAPI app, orchestrator, agents, backend tests
- `frontend/` - Next.js app, UI pages/components, frontend tests
- `docs/` - architecture, deployment, checklists, runbooks
- `scripts/` - bootstrap and verification scripts
- `.github/workflows/` - CI workflows

## Deployment Summary

- **Vercel:** frontend only (recommended for UI hosting)
- **GitHub Pages:** static frontend only
- **Full stack:** VM/containers or split deploy (frontend + separate backend)

See `docs/DEPLOY_FULL_STACK.md` for production deployment options.

## Troubleshooting

### Backend imports or startup errors

- Ensure Python 3.11 is used.
- Re-run bootstrap script.

### Frontend loads but API calls fail

- Confirm backend is running on `127.0.0.1:8000`.
- Check `frontend/.env.local` (`BACKEND_URL`).

### Port already in use

- Frontend: `npm run dev -- -p 3001`
- Backend: `--port 8001` and update `BACKEND_URL`

### Vercel says "No Next.js version detected"

- Recommended project root directory on Vercel: `frontend/`
- Root `package.json` and `vercel.json` are included for root-mode fallback

## Additional Documentation

- `docs/ARCHITECTURE.md`
- `docs/IMPLEMENTATION_PROGRESS.md`
- `docs/DEPLOY_FULL_STACK.md`
- `docs/PIPELINE-MANUAL-TEST-CHECKLIST.md`
- `docs/RELEASE_CHECKLIST.md`
