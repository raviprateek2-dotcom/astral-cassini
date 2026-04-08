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
async def test_workflow_recommendations_includes_decision_traces(client, db):
    """GET /api/workflow/{job_id}/recommendations exposes decision_traces from workflow state."""
    from app.core.auth import get_current_user
    from app.models.db_models import Job, User

    app.dependency_overrides[get_current_user] = lambda: User(id=1, email="hr@prohr.ai")

    job = Job(
        job_id="trc-job1",
        job_title="Trace Test",
        department="Eng",
        current_stage="decision",
        workflow_state={
            "final_recommendations": [
                {
                    "candidate_id": "c-trace",
                    "candidate_name": "Sam Trace",
                    "decision": "hire",
                    "confidence": 81.0,
                    "screening_weight": 32.0,
                    "interview_weight": 49.0,
                    "overall_weighted_score": 81.0,
                    "reasoning": "Unit test",
                    "risk_factors": [],
                }
            ],
            "decision_traces": [
                {
                    "candidate_id": "c-trace",
                    "candidate_name": "Sam Trace",
                    "screening_score": 80.0,
                    "interview_score_scaled": 81.5,
                    "concerns_count": 0,
                    "weighted_score": 81.0,
                    "decision": "hire",
                    "rule_applied": "weighted>=75&&concerns<3=>hire",
                }
            ],
        },
    )
    db.add(job)
    db.commit()

    response = client.get("/api/workflow/trc-job1/recommendations")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["job_id"] == "trc-job1"
    assert len(data["final_recommendations"]) == 1
    assert len(data["decision_traces"]) == 1
    assert data["decision_traces"][0]["candidate_id"] == "c-trace"
    assert data["decision_traces"][0]["rule_applied"]

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


@pytest.mark.asyncio
async def test_websocket_connects_with_ws_ticket(client, db):
    """End-to-end WS auth path: cookie session -> ws-ticket -> /ws connect."""
    from sqlalchemy.orm import sessionmaker

    from app.api import websocket as websocket_api
    from app.core.auth import create_access_token, hash_password
    from app.core.orchestrator import start_workflow
    from app.models.db_models import User

    user = User(
        email="ws-connect-test@example.com",
        full_name="WS Connect Test",
        hashed_password=hash_password("unused"),
        role="hr_manager",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    result = await start_workflow(db, int(user.id), "WS Connect Role", "Eng", ["Python"])
    job_id = result["job_id"]

    token = create_access_token({"sub": str(int(user.id)), "role": str(user.role)})
    client.cookies.set("access_token", token)

    ticket_res = client.get("/api/auth/ws-ticket", params={"job_id": job_id})
    assert ticket_res.status_code == status.HTTP_200_OK
    ticket = ticket_res.json()["ticket"]

    # websocket.py imports SessionLocal at module import time; bind it to test DB for this test.
    websocket_api.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db.get_bind(),
    )

    with client.websocket_connect(f"/ws/{job_id}?token={ticket}") as ws:
        first = ws.receive_json()
        assert first["type"] == "connected"
        assert first["job_id"] == job_id
        assert first["data"]["current_stage"] == PipelineStage.JD_DRAFTING.value


@pytest.mark.asyncio
async def test_observability_metrics_admin_only(client):
    from app.core.auth import get_current_user
    from app.models.db_models import User

    app.dependency_overrides[get_current_user] = lambda: User(
        id=1,
        email="admin@prohr.ai",
        role="admin",
        is_active=True,
    )
    response = client.get("/api/analytics/observability")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "observability" in body
    assert "ws_ticket_issued" in body["observability"]

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_observability_metrics_forbidden_for_non_admin(client):
    from app.core.auth import get_current_user
    from app.models.db_models import User

    app.dependency_overrides[get_current_user] = lambda: User(
        id=2,
        email="hr@prohr.ai",
        role="hr_manager",
        is_active=True,
    )
    response = client.get("/api/analytics/observability")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_prometheus_metrics_admin_only(client):
    from app.core.auth import get_current_user
    from app.models.db_models import User

    app.dependency_overrides[get_current_user] = lambda: User(
        id=3,
        email="admin2@prohr.ai",
        role="admin",
        is_active=True,
    )
    response = client.get("/api/analytics/metrics")
    assert response.status_code == status.HTTP_200_OK
    assert "text/plain" in response.headers.get("content-type", "")
    body = response.text
    assert "prohr_ws_ticket_issued_total" in body
    assert "prohr_ws_connect_success_total" in body

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_prometheus_metrics_forbidden_for_non_admin(client):
    from app.core.auth import get_current_user
    from app.models.db_models import User

    app.dependency_overrides[get_current_user] = lambda: User(
        id=4,
        email="viewer@prohr.ai",
        role="viewer",
        is_active=True,
    )
    response = client.get("/api/analytics/metrics")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    app.dependency_overrides.pop(get_current_user)
