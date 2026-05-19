import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from jose import jwt
from app.models.db_models import Job, User
from app.core.auth import SECRET_KEY, ALGORITHM, WS_TOKEN_AUDIENCE
from app.config import settings

def test_ws_rejection_without_token(client: TestClient):
    # Make sure auth_bypass is false
    settings.auth_disabled = False
    
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/some-job-id"):
            pass
    assert exc.value.code == 4401

def test_ws_rejection_mismatch(client: TestClient):
    settings.auth_disabled = False
    payload = {"sub": "1", "job_id": "other-job", "aud": WS_TOKEN_AUDIENCE}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/my-job?token={token}"):
            pass
    assert exc.value.code == 4403

def test_ws_successful_connection_and_heartbeat(client: TestClient, db):
    settings.auth_disabled = False
    user = User(
        email="testws@prohr.ai",
        full_name="WS Tester",
        hashed_password="pw",
        role="admin",
        department="HR",
        is_active=True
    )
    db.add(user)
    db.commit()

    job = Job(
        job_id="test-job-ws",
        job_title="Test Job",
        department="HR",
        current_stage="jd_drafting",
        workflow_state={"state": {}}
    )
    db.add(job)
    db.commit()

    payload = {"sub": str(user.id), "job_id": "test-job-ws", "aud": WS_TOKEN_AUDIENCE}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    with client.websocket_connect(f"/ws/test-job-ws?token={token}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "connected"
        assert msg["job_id"] == "test-job-ws"
        
        ws.send_json({"type": "ping"})
        msg = ws.receive_json()
        assert msg["type"] == "pong"
