# Contributing Guide

## Branch and PR Flow

1. Create a feature branch from `master`.
2. Keep changes scoped and include tests.
3. Run local verification before opening a PR:
   - `bash scripts/verify-backend.sh`
   - `bash scripts/verify-frontend.sh`
4. Open PR with:
   - summary of why the change is needed
   - test plan
   - rollback considerations (if behavior/security related)

## Coding Expectations

- Keep APIs backward compatible unless migration notes are provided.
- Avoid committing secrets (`.env`, credentials, tokens, generated auth state).
- Add/adjust tests for behavior changes.
- Update docs for config/env/route changes.

## Commit Messages

- Use imperative style.
- Explain intent and impact, not just file edits.

## Local Setup

- Backend: `cd backend && pip install -r requirements.txt`
- Frontend: `cd frontend && npm install`
- Start app:
  - backend: `uvicorn app.main:app --reload`
  - frontend: `npm run dev`

## Security and Disclosure

See `SECURITY.md` for vulnerability reporting.
