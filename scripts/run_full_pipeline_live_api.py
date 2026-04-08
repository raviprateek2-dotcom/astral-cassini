#!/usr/bin/env python3
"""
Walk one recruitment job through every HTTP API stage until the pipeline completes.

Requires a running FastAPI server. Typical dev setup::

  cd backend
  set SECRET_KEY=ci-test-secret-key-must-be-32chars-minimum
  set APP_ENV=development
  set SEED_DEMO_USERS=true
  set DEMO_ADMIN_PASSWORD=adminpass12345
  set DEMO_HR_PASSWORD=hrpass12345678
  uvicorn app.main:app --host 127.0.0.1 --port 8000

Then from repo root::

  python scripts/run_full_pipeline_live_api.py

Environment (optional):
  PIPELINE_API_BASE   default http://127.0.0.1:8000
  PIPELINE_HR_EMAIL   default hr@prohr.ai
  PIPELINE_HR_PASSWORD  default DEMO_HR_PASSWORD value you configured
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

import httpx

TIMEOUT = httpx.Timeout(120.0, connect=30.0)


def _log(step: int, title: str, detail: str = "") -> None:
    bar = "─" * 60
    print(f"\n{bar}\n  STEP {step}: {title}")
    if detail:
        print(f"  {detail}\n{bar}")


def main() -> int:
    base = os.environ.get("PIPELINE_API_BASE", "http://127.0.0.1:8000").rstrip("/")
    email = os.environ.get("PIPELINE_HR_EMAIL", "hr@prohr.ai")
    password = os.environ.get("PIPELINE_HR_PASSWORD", os.environ.get("DEMO_HR_PASSWORD", ""))
    if not password:
        print(
            "Set PIPELINE_HR_PASSWORD or DEMO_HR_PASSWORD (8+ chars) for the seeded HR user.",
            file=sys.stderr,
        )
        return 1

    api = f"{base}/api"

    with httpx.Client(timeout=TIMEOUT) as client:
        _log(1, "Authenticate (HR)", f"POST /api/auth/login as {email}")
        r = client.post(
            f"{api}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r.status_code != 200:
            print(f"Login failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1
        token = r.json().get("access_token", "")
        cookies = r.cookies
        headers = {"Authorization": f"Bearer {token}"}

        _log(2, "Job intake", "POST /api/jobs — starts JD drafting in background")
        payload = {
            "job_title": "Live Pipeline API Test",
            "department": "Engineering",
            "requirements": ["Python", "Testing"],
            "preferred_qualifications": [],
            "location": "Remote",
            "salary_range": "Competitive",
        }
        r = client.post(f"{api}/jobs", json=payload, headers=headers, cookies=cookies)
        if r.status_code != 200:
            print(f"Create job failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1
        job_id = r.json()["job_id"]
        print(f"  job_id={job_id}")

        def get_job() -> dict[str, Any]:
            rr = client.get(f"{api}/jobs/{job_id}", headers=headers, cookies=cookies)
            rr.raise_for_status()
            return rr.json()

        def wait_for(predicate, desc: str, timeout_s: float = 180.0) -> dict[str, Any]:
            deadline = time.time() + timeout_s
            last = {}
            while time.time() < deadline:
                last = get_job()
                if predicate(last):
                    return last
                time.sleep(0.4)
            raise TimeoutError(f"Timeout waiting for: {desc}; last stage={last.get('current_stage')}")

        # 3) Wait for first HITL: jd_review
        _log(3, "Wait for JD review (Agent 1 → Liaison gate)")
        wait_for(
            lambda j: j.get("current_stage") == "jd_review"
            and (j.get("state") or {}).get("jd_approval") == "pending",
            "jd_review with jd_approval pending",
        )
        print("  At jd_review — approving.")

        # 4) JD approval
        _log(4, "HITL: Approve JD", "POST /api/workflow/{job_id}/approve")
        r = client.post(
            f"{api}/workflow/{job_id}/approve",
            json={"feedback": "Approved for sourcing."},
            headers=headers,
            cookies=cookies,
        )
        if r.status_code != 200:
            print(f"JD approve failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1

        # 5) Scout + Screener → shortlist_review
        _log(5, "Automated sourcing & screening → shortlist gate")
        wait_for(
            lambda j: j.get("current_stage") == "shortlist_review"
            and (j.get("state") or {}).get("shortlist_approval") == "pending",
            "shortlist_review pending",
            timeout_s=240.0,
        )
        print(f"  Scored candidates: {len((get_job().get('state') or {}).get('scored_candidates') or [])}")

        _log(6, "HITL: Approve shortlist", "POST /api/workflow/{job_id}/approve")
        r = client.post(
            f"{api}/workflow/{job_id}/approve",
            json={"feedback": "Proceed to outreach and interviews."},
            headers=headers,
            cookies=cookies,
        )
        if r.status_code != 200:
            print(f"Shortlist approve failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1

        # 7) Outreach → … → hire_review
        _log(
            7,
            "Automated outreach → engagement → scheduling → interview → decision",
            "Wait for hire_review",
        )
        wait_for(
            lambda j: j.get("current_stage") == "hire_review"
            and (j.get("state") or {}).get("hire_approval") == "pending",
            "hire_review pending",
            timeout_s=300.0,
        )

        _log(8, "HITL: Final hire approval", "POST /api/workflow/{job_id}/approve")
        r = client.post(
            f"{api}/workflow/{job_id}/approve",
            json={"feedback": "Confirm hire; generate offer."},
            headers=headers,
            cookies=cookies,
        )
        if r.status_code != 200:
            print(f"Hire approve failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1

        _log(9, "Offer generation → completed", "Wait for current_stage == completed")
        wait_for(lambda j: j.get("current_stage") == "completed", "completed", timeout_s=180.0)
        final = get_job()
        st = final.get("state") or {}
        offers = st.get("offer_details") or []
        print(f"  Completed with {len(offers)} offer record(s).")
        audit = st.get("audit_log") or []
        if audit:
            print(f"  Audit tail: {audit[-1].get('action')} @ {audit[-1].get('stage')}")

        _log(10, "Done", "Full pipeline reached COMPLETED via live HTTP API.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
