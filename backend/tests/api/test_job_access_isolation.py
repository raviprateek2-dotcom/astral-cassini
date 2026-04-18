"""Regression: job-scoped APIs must not leak across non-admin users."""

from __future__ import annotations

import uuid

import pytest
from starlette import status

pytestmark = pytest.mark.api

from app.core.auth import get_current_user, hash_password
from app.main import app
from app.models.db_models import User


@pytest.mark.asyncio
async def test_get_job_forbidden_for_other_hr_manager(client, db):
    """Another hr_manager must not read a job they did not create (non-admin)."""
    owner = User(
        email="owner-job-access@prohr-e2e.xyz",
        full_name="Owner",
        hashed_password=hash_password("unused-password-A1!"),
        role="hr_manager",
        department="Eng",
    )
    intruder = User(
        email="intruder-job-access@prohr-e2e.xyz",
        full_name="Intruder",
        hashed_password=hash_password("unused-password-B1!"),
        role="hr_manager",
        department="Eng",
    )
    db.add(owner)
    db.add(intruder)
    db.commit()
    db.refresh(owner)
    db.refresh(intruder)

    from app.core.orchestrator import start_workflow

    result = await start_workflow(
        db,
        int(owner.id),
        "Isolation Role",
        "QA",
        ["Testing"],
    )
    job_id = result["job_id"]

    app.dependency_overrides[get_current_user] = lambda: intruder
    try:
        res = client.get(f"/api/jobs/{job_id}")
        assert res.status_code == status.HTTP_403_FORBIDDEN
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_job_allowed_for_admin_even_when_not_owner(client, db):
    """Admin may read any job (policy: user_can_access_job)."""
    owner = User(
        email="owner-admin-read@prohr-e2e.xyz",
        full_name="Owner2",
        hashed_password=hash_password("unused-password-C1!"),
        role="hr_manager",
        department="Eng",
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    from app.core.orchestrator import start_workflow

    result = await start_workflow(db, int(owner.id), "Admin Read Job", "QA", ["x"])
    job_id = result["job_id"]

    admin = User(
        id=42,
        email="admin-readall@prohr-e2e.xyz",
        full_name="Admin",
        hashed_password=hash_password("unused-password-D1!"),
        role="admin",
        department="Ops",
    )

    app.dependency_overrides[get_current_user] = lambda: admin
    try:
        res = client.get(f"/api/jobs/{job_id}")
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["job_id"] == job_id
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_workflow_and_candidates_forbidden_for_other_hr_manager(client, db):
    """Non-owner hr_manager must not read or mutate another user's pipeline."""
    u = uuid.uuid4().hex[:12]
    owner = User(
        email=f"wf-owner-{u}@prohr-e2e.xyz",
        full_name="WF Owner",
        hashed_password=hash_password("unused-password-W1!"),
        role="hr_manager",
        department="Eng",
    )
    intruder = User(
        email=f"wf-intruder-{u}@prohr-e2e.xyz",
        full_name="WF Intruder",
        hashed_password=hash_password("unused-password-W2!"),
        role="hr_manager",
        department="Eng",
    )
    db.add(owner)
    db.add(intruder)
    db.commit()
    db.refresh(owner)
    db.refresh(intruder)

    from app.core.orchestrator import start_workflow

    result = await start_workflow(db, int(owner.id), "WF Isolation", "QA", ["x"])
    job_id = result["job_id"]

    app.dependency_overrides[get_current_user] = lambda: intruder
    try:
        paths_get = (
            f"/api/workflow/{job_id}/status",
            f"/api/workflow/{job_id}/audit",
            f"/api/workflow/{job_id}/interviews",
            f"/api/workflow/{job_id}/recommendations",
            f"/api/jobs/{job_id}/candidates",
        )
        for path in paths_get:
            res = client.get(path)
            assert res.status_code == status.HTTP_403_FORBIDDEN, f"GET {path} -> {res.status_code} {res.text}"
        res = client.post(f"/api/workflow/{job_id}/approve", json={"feedback": ""})
        assert res.status_code == status.HTTP_403_FORBIDDEN, res.text
        res = client.post(f"/api/workflow/{job_id}/reject", json={"feedback": "go away"})
        assert res.status_code == status.HTTP_403_FORBIDDEN, res.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)
