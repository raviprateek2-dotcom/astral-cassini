import pytest

pytestmark = pytest.mark.api

from starlette import status
from app.models.state import PipelineStage
from app.main import app

@pytest.mark.asyncio
async def test_endpoint_create_job(client):
    """Verify POST /api/jobs initializes a new requisition."""
    
    # Mocking Auth via get_current_user
    from app.core.auth import get_current_user
    from app.models.db_models import User
    
    # Make sure to mock a user with required role
    mock_user = User(id=1, email="hr@prohr.ai", role="hr_manager")
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {
        "job_title": "Senior DevOps Engineer",
        "department": "Infrastructure",
        "requirements": ["Kubernetes", "AWS", "Terraform"],
        "location": "Remote",
        "salary_range": "150k - 180k"
    }
    
    response = client.post("/api/jobs", json=payload)
    
    assert response.status_code == status.HTTP_200_OK # Router says response_model=JobResponse, usually 201 if specified but default is 200
    data = response.json()
    assert data["job_id"] is not None
    assert data["current_stage"] == PipelineStage.JD_DRAFTING.value
    
    app.dependency_overrides.pop(get_current_user)

@pytest.mark.asyncio
async def test_endpoint_get_state(client, db):
    """Verify GET /api/jobs/{job_id} returns the current state."""
    
    # Mocking Auth
    from app.core.auth import get_current_user
    from app.models.db_models import User
    app.dependency_overrides[get_current_user] = lambda: User(id=1, email="hr@prohr.ai")

    # Create mock job via internal function
    from app.core.orchestrator import start_workflow
    result = await start_workflow(db, 1, "Staff Scientist", "Research", ["ML", "Physics"])
    job_id = result["job_id"]
    
    response = client.get(f"/api/jobs/{job_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["job_id"] == job_id
    
    app.dependency_overrides.pop(get_current_user)

@pytest.mark.asyncio
async def test_endpoint_approve_jd(client, db):
    """Verify POST /api/workflow/{job_id}/approve moves the state machine forward."""
    
    from app.core.auth import get_current_user
    from app.models.db_models import User
    app.dependency_overrides[get_current_user] = lambda: User(id=1, email="hr@prohr.ai", role="hr_manager")

    from app.core.orchestrator import start_workflow
    result = await start_workflow(db, 1, "Staff Scientist", "Research", ["ML", "Physics"])
    job_id = result["job_id"]
    
    # Manually force state to review
    from app.models.db_models import Job
    job = db.query(Job).filter(Job.job_id == job_id).first()
    state = result["state"]
    state["current_stage"] = PipelineStage.JD_REVIEW.value
    job.workflow_state = state
    job.current_stage = PipelineStage.JD_REVIEW.value
    db.commit()
    
    # APPROVE JD
    payload = {"feedback": "LGTM", "updated_jd": "Revised text"}
    response = client.post(f"/api/workflow/{job_id}/approve", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["jd_approval"] == "approved"
    assert data["current_stage"] == PipelineStage.SOURCING.value
    
    app.dependency_overrides.pop(get_current_user)

@pytest.mark.asyncio
async def test_endpoint_not_found(client, db):
    """Ensure API returns 404 for invalid job IDs."""
    
    # Mocking Auth
    from app.core.auth import get_current_user
    from app.models.db_models import User
    app.dependency_overrides[get_current_user] = lambda: User(id=1, email="hr@prohr.ai")

    response = client.get("/api/jobs/invalid-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_ws_ticket_for_job(client, db):
    """GET /api/auth/ws-ticket returns a short-lived JWT bound to job_id."""
    from jose import jwt as jose_jwt

    from app.core.auth import (
        ALGORITHM,
        SECRET_KEY,
        WS_TOKEN_AUDIENCE,
        create_access_token,
        hash_password,
    )
    from app.core.orchestrator import start_workflow
    from app.models.db_models import User

    user = User(
        email="ws-ticket-test@example.com",
        full_name="WS Ticket Test",
        hashed_password=hash_password("unused"),
        role="hr_manager",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    result = await start_workflow(db, user.id, "WS Test Role", "Eng", ["Python"])
    job_id = result["job_id"]

    token = create_access_token({"sub": str(user.id), "role": user.role})
    client.cookies.set("access_token", token)
    response = client.get("/api/auth/ws-ticket", params={"job_id": job_id})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "ticket" in body
    assert body.get("aud") == WS_TOKEN_AUDIENCE
    decoded = jose_jwt.decode(
        body["ticket"], SECRET_KEY, algorithms=[ALGORITHM], audience=WS_TOKEN_AUDIENCE
    )
    assert decoded["job_id"] == job_id
    assert decoded["sub"] == str(user.id)


@pytest.mark.asyncio
async def test_ws_ticket_unknown_job(client, db):
    from app.core.auth import create_access_token, hash_password
    from app.models.db_models import User

    user = User(
        email="ws-ticket-404@example.com",
        full_name="WS 404 Test",
        hashed_password=hash_password("unused"),
        role="hr_manager",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    client.cookies.set("access_token", token)
    response = client.get("/api/auth/ws-ticket", params={"job_id": "nope-nope"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
