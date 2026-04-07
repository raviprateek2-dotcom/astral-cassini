"""Improved WebSocket endpoint — real-time streaming of agent events.

Improvements over v1:
- Streams JD generation token-by-token (async streaming from OpenAI)
- Broadcasts agent stage transitions to ALL connected clients for a job
- Ping/pong heartbeat to detect dropped connections
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.config import settings
from app.core.database import SessionLocal
from app.core.auth import (
    ALGORITHM,
    SECRET_KEY,
    WS_TOKEN_AUDIENCE,
    user_may_subscribe_job_ws,
)
from app.models.db_models import Job, User



router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger(__name__)

# job_id → list of connected WebSocket clients
_connections: dict[str, list[WebSocket]] = defaultdict(list)


async def broadcast(job_id: str, event_type: str, data: dict) -> None:
    """Broadcast a structured event to all clients watching job_id."""
    payload = json.dumps({"type": event_type, "job_id": job_id, "data": data})
    dead: list[WebSocket] = []
    for ws in list(_connections[job_id]):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _connections[job_id]:
            _connections[job_id].remove(ws)


async def emit_pipeline_snapshot(job_id: str) -> None:
    """Push full workflow snapshot to all subscribers (call after DB state changes)."""
    try:
        with SessionLocal() as db:
            from app.core.orchestrator import get_workflow_status

            status = get_workflow_status(db, job_id)
        if not status:
            return
        state = status.get("state") or {}
        if not isinstance(state, dict):
            state = {}
        current_stage = status.get("current_stage", "")
        await broadcast(
            job_id,
            "pipeline_update",
            {
                "current_stage": current_stage,
                "state": state,
            },
        )
    except Exception as e:
        logger.warning("emit_pipeline_snapshot failed job=%s: %s", job_id, e)


def schedule_pipeline_snapshot(job_id: str) -> None:
    """Fire-and-forget notify when a running event loop exists (e.g. API / orchestration)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    loop.create_task(emit_pipeline_snapshot(job_id))


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """Real-time pipeline status stream for a specific job.

    Events emitted:
    - `connected`        — on join, with current stage
    - `pipeline_update`  — broadcast when workflow state is saved (all subscribers)
    - `heartbeat`        — infrequent per-client sync if idle (~60s without ping)
    - `pong`            — heartbeat response
    - `stream_token`    — JD streaming tokens (optional)
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401, reason="Missing token")
        return

    with SessionLocal() as db:
        user: User | None = None
        job = db.query(Job).filter(Job.job_id == job_id).first()

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=WS_TOKEN_AUDIENCE)
        except JWTError:
            payload = None

        if payload is not None:
            if payload.get("job_id") != job_id:
                await websocket.close(code=4403, reason="Ticket job mismatch")
                return
            uid = payload.get("sub")
            user = db.get(User, int(uid)) if uid else None
            if user and user.is_active and job and user_may_subscribe_job_ws(user, job):
                pass
            else:
                user = None
        else:
            if not settings.ws_allow_legacy_browser_token:
                await websocket.close(code=4401, reason="Invalid or expired ticket")
                return
            try:
                legacy = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
            except JWTError:
                await websocket.close(code=4401, reason="Unauthorized")
                return
            if legacy.get("aud") == WS_TOKEN_AUDIENCE:
                await websocket.close(code=4401, reason="Unauthorized")
                return
            uid = legacy.get("sub")
            user = db.get(User, int(uid)) if uid else None
            if not user or not user.is_active:
                await websocket.close(code=4401, reason="Unauthorized")
                return
            if not job:
                await websocket.close(code=4404, reason="Job not found")
                return
            if not user_may_subscribe_job_ws(user, job):
                await websocket.close(code=4403, reason="Forbidden")
                return

    if not job:
        await websocket.close(code=4404, reason="Job not found")
        return
    if not user or not user.is_active:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    await websocket.accept()
    _connections[job_id].append(websocket)
    logger.info(f"WS connected: user={user.id}, job={job_id}, total={len(_connections[job_id])}")

    # Send initial state
    with SessionLocal() as db:
        from app.core.orchestrator import get_workflow_status
        status = get_workflow_status(db, job_id)
    await websocket.send_json({
        "type": "connected",
        "job_id": job_id,
        "data": {
            "current_stage": status.get("current_stage", "unknown") if status else "not_found",
            "job_title": status.get("job_title", "") if status else "",
        },
    })

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                if raw.startswith("{"):
                    msg = json.loads(raw)
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                elif raw.strip().lower() == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                raw = None
            except json.JSONDecodeError:
                continue

            # Infrequent per-client sync if client idle (broadcasts cover the hot path)
            if raw is None:
                with SessionLocal() as db:
                    from app.core.orchestrator import get_workflow_status

                    current_status = get_workflow_status(db, job_id)
                if current_status:
                    state = current_status.get("state") or {}
                    if not isinstance(state, dict):
                        state = {}
                    current_stage = current_status.get("current_stage", "")
                    candidates_count = len(state.get("candidates", []) or [])
                    await websocket.send_json(
                        {
                            "type": "heartbeat",
                            "job_id": job_id,
                            "data": {
                                "current_stage": current_stage,
                                "state": state,
                                "candidates": candidates_count,
                                "scored": len(state.get("scored_candidates", []) or []),
                                "interviews": len(state.get("scheduled_interviews", []) or []),
                            },
                        }
                    )

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: job={job_id}")
    except Exception as e:
        logger.error(f"WS error job={job_id}: {e}")
    finally:
        if websocket in _connections[job_id]:
            _connections[job_id].remove(websocket)


async def stream_jd_tokens(job_id: str, token: str) -> None:
    """Called by JD Architect during streaming to push individual tokens."""
    await broadcast(job_id, "stream_token", {"token": token})
