"""Workflow API routes — HITL approval/rejection and audit trail."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, RequireHR
from app.models.db_models import User
from app.core.orchestrator import (
    approve_stage,
    reject_stage,
    get_workflow_status,
    resume_workflow,
)

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


class ApprovalRequest(BaseModel):
    """Request body for approving/rejecting a stage."""
    feedback: str = ""
    updated_jd: str | None = None # For JD refinement stage


@router.post("/{job_id}/approve")
async def approve(
    job_id: str,
    req: ApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, RequireHR],
):
    """Approve the current HITL gate and resume the workflow (HR only)."""
    result = await approve_stage(db, job_id, feedback=req.feedback, updated_jd=req.updated_jd)
    if result.get("error") and result.get("status") != "running":
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{job_id}/reject")
async def reject(
    job_id: str,
    req: ApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, RequireHR],
):
    """Reject the current HITL gate with feedback (HR only)."""
    if not req.feedback:
        raise HTTPException(
            status_code=400,
            detail="Feedback is required for rejection"
        )
    result = await reject_stage(db, job_id, feedback=req.feedback)
    if result.get("error") and result.get("status") != "running":
        raise HTTPException(status_code=400, detail=result["error"])
    return result


class PatchStateRequest(BaseModel):
    action: str
    state_updates: dict

@router.patch("/{job_id}/state")
async def patch_state(
    job_id: str,
    req: PatchStateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireHR],
):
    """Manually update the workflow state and resume execution.
    Useful for E2E testing and agent-override scenarios.
    """
    try:
        result = await resume_workflow(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            action=req.action,
            state_updates=req.state_updates
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/status")
async def get_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Get current pipeline stage for a job."""
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {
        "job_id": job_id,
        "current_stage": status.get("current_stage", "unknown"),
        "job_title": status.get("job_title", ""),
    }


@router.get("/{job_id}/audit")
async def get_audit(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Get the full audit trail for a job."""
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    state = status.get("state", {})
    return {
        "job_id": job_id,
        "audit_log": state.get("audit_log", []),
    }


@router.get("/{job_id}/interviews")
async def get_interviews(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Get scheduled interviews and assessments for a job."""
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    state = status.get("state", {})
    return {
        "job_id": job_id,
        "scheduled_interviews": state.get("scheduled_interviews", []),
        "interview_assessments": state.get("interview_assessments", []),
    }


@router.get("/{job_id}/recommendations")
async def get_recommendations(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Get final hire/no-hire recommendations for a job."""
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    state = status.get("state", {})
    return {
        "job_id": job_id,
        "final_recommendations": state.get("final_recommendations", []),
    }
