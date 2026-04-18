# Pipeline Manual Test Checklist

> **HUMAN VERIFICATION REQUIRED**  
> Only a **person** performing these steps in a real environment (browser + API) can mark items complete. **Do not** treat pre-checked boxes or CI as proof — reset boxes to `[ ]` when starting a new validation pass and record date + initials in your runbook or issue.

Use this while validating one job pipeline end-to-end in the UI.

## Setup
- [x] Backend running at `http://127.0.0.1:8000`
- [x] Frontend running at `http://127.0.0.1:3000`
- [x] Logged in as an HR/Admin user
- [x] Created a new job in `Jobs` page and noted `job_id`

## Gate 1: JD Review (`jd_review`)
- [x] Pipeline reaches `jd_review`
- [x] Reject once with feedback
- [x] Confirm stage moves back to `jd_drafting`
- [x] Approve once with feedback
- [x] Confirm stage advances to sourcing flow

## Gate 2: Shortlist Review (`shortlist_review`)
- [x] Pipeline reaches `shortlist_review`
- [x] Reject once with feedback
- [x] Confirm stage moves back to `sourcing`
- [x] Approve once with feedback
- [x] Confirm stage advances to outreach/interview flow

## Gate 3: Final Hire Review (`hire_review`)
- [x] Pipeline reaches `hire_review`
- [x] Reject once with feedback
- [x] Confirm stage moves back to `decision`
- [x] Approve once with feedback
- [x] Confirm stage advances to `offer` then `completed`

## Page-level validation
- [x] `Interviews` page shows scheduled interviews for the selected job
- [x] `Decisions` page shows recommendation + decision trace
- [x] `Audit` page reflects approve/reject actions with timestamps

## API spot checks (optional)
- [x] `GET /api/workflow/{job_id}/status` matches UI stage
- [x] `GET /api/workflow/{job_id}/audit` includes gate actions

## Automated regression run
- [ ] Backend: `pytest tests -q` (from `backend/`; includes API job-access isolation tests)
- [ ] Playwright smoke: `cd frontend && npm run test:e2e` (mocked API)
- [ ] Playwright full-stack: `cd frontend && npm run build && npm run test:e2e:full` (`PLAYWRIGHT_FULL_STACK=1`; covers authenticated **Interviews**, **Decisions**, **Approvals**, **Audit** stubs in `e2e/app.authenticated.spec.ts`)
- Progress tracker: [IMPLEMENTATION_PROGRESS.md](./IMPLEMENTATION_PROGRESS.md)
