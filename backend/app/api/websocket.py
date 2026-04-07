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
from app.core.database import SessionLocal



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


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """Real-time pipeline status stream for a specific job.

    Events emitted:
    - `connected`     — on join, with current stage
    - `stage_change`  — when the pipeline moves to a new stage
    - `pong`          — heartbeat response
    - `stream_token`  — individual JD streaming tokens (future)
    """
    await websocket.accept()
    _connections[job_id].append(websocket)
    logger.info(f"WS connected: job={job_id}, total={len(_connections[job_id])}")

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

    last_stage = status.get("current_stage", "") if status else ""
    last_candidates_count = 0

    try:
        while True:
            # Non-blocking receive with timeout for polling
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=3.0)
                msg = json.loads(raw) if raw.startswith("{") else {"type": raw}
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                pass  # No message received — just poll for updates

            except json.JSONDecodeError:
                pass

            # Poll for pipeline state changes
            with SessionLocal() as db:
                from app.core.orchestrator import get_workflow_status
                current_status = get_workflow_status(db, job_id)
            if current_status:
                current_stage = current_status.get("current_stage", "")
                state = current_status.get("state", {})
                candidates_count = len(state.get("candidates", []))

                # Stage transition event
                if current_stage != last_stage:
                    await broadcast(job_id, "stage_change", {
                        "previous_stage": last_stage,
                        "current_stage": current_stage,
                        "job_title": current_status.get("job_title", ""),
                    })
                    last_stage = current_stage

                # Candidates loaded event
                if candidates_count != last_candidates_count and candidates_count > 0:
                    await broadcast(job_id, "candidates_found", {
                        "count": candidates_count,
                        "stage": current_stage,
                    })
                    last_candidates_count = candidates_count

                # Heartbeat with stage summary every 10s
                await websocket.send_json({
                    "type": "heartbeat",
                    "job_id": job_id,
                    "data": {
                        "current_stage": current_stage,
                        "candidates": candidates_count,
                        "scored": len(state.get("scored_candidates", [])),
                        "interviews": len(state.get("scheduled_interviews", [])),
                    },
                })

            await asyncio.sleep(1)  # Poll every 1s for near real-time responsiveness

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
