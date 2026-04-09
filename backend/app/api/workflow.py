"""Workflow API routes — HITL approval/rejection and audit trail."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user, RequireHR, require_job_access
from app.models.db_models import User
from app.models.state import Assessment, DecisionTrace, Recommendation
from app.tools.email_tool import send_interview_invitation
from app.config import settings
from app.core.orchestrator import (
    approve_stage,
    reject_stage,
    get_workflow_status,
    resume_workflow,
    append_candidate_response,
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
    current_user: Annotated[User, RequireHR],
):
    """Approve the current HITL gate and resume the workflow (HR only)."""
    require_job_access(db, current_user, job_id)
    try:
        result = await approve_stage(db, job_id, feedback=req.feedback, updated_jd=req.updated_jd)
        if result.get("error") and result.get("status") != "running":
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{job_id}/reject")
async def reject(
    job_id: str,
    req: ApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireHR],
):
    """Reject the current HITL gate with feedback (HR only)."""
    require_job_access(db, current_user, job_id)
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
    action: str = "manual_patch"
    reason: str = ""
    state_updates: dict


class CandidateResponseRequest(BaseModel):
    candidate_id: str
    candidate_name: str
    response: str


class InterviewInviteRequest(BaseModel):
    candidate_id: str = ""
    candidate_name: str
    to_email: str
    meeting_link: str
    interview_type: str = "technical"
    scheduled_time: str = ""
    duration_minutes: int = 60
    interviewers: list[str] = []


class InterviewCompletionRequest(BaseModel):
    candidate_id: str
    candidate_name: str
    selected: bool
    technical_score: float = 0.0
    communication_score: float = 0.0
    problem_solving_score: float = 0.0
    cultural_fit_score: float = 0.0
    observations: list[str] = []
    concerns: list[str] = []


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
        require_job_access(db, current_user, job_id)
        if str(current_user.role) != "admin":
            raise HTTPException(status_code=403, detail="Manual state patch is admin-only")
        if str(settings.app_env).lower() == "production":
            raise HTTPException(status_code=403, detail="Manual state patch is disabled in production")
        allowed_fields = {
            "current_stage",
            "human_feedback",
            "job_description",
            "jd_approval",
            "shortlist_approval",
            "hire_approval",
            "candidates",
            "scored_candidates",
            "scheduled_interviews",
            "interview_assessments",
            "final_recommendations",
            "decision_traces",
            "candidate_responses",
            "offer_details",
            "error",
        }
        disallowed = [k for k in req.state_updates.keys() if k not in allowed_fields]
        if disallowed:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported state update keys: {', '.join(sorted(disallowed))}",
            )
        audit_detail = req.reason or f"Manual patch keys: {', '.join(sorted(req.state_updates.keys()))}"
        result = await resume_workflow(
            db=db,
            user_id=int(current_user.id),
            job_id=job_id,
            action="manual_patch",
            state_updates={**req.state_updates, "human_feedback": audit_detail},
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{job_id}/interview-invite")
async def interview_invite(
    job_id: str,
    req: InterviewInviteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireHR],
):
    """HR action: create/send interview meeting link to a candidate."""
    require_job_access(db, current_user, job_id)
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    state = status.get("state", {}) or {}
    interviews = state.get("scheduled_interviews", [])
    if not isinstance(interviews, list):
        interviews = []

    row = {
        "id": f"manual-{req.candidate_id or req.candidate_name}",
        "candidate_id": req.candidate_id,
        "candidate_name": req.candidate_name,
        "interview_type": req.interview_type,
        "scheduled_time": req.scheduled_time,
        "duration_minutes": req.duration_minutes,
        "interviewers": req.interviewers,
        "meeting_link": req.meeting_link,
        "status": "scheduled",
    }
    interviews.append(row)
    send_interview_invitation(
        to_email=req.to_email,
        candidate_name=req.candidate_name,
        job_title=status.get("job_title", "Role"),
        interview_time=req.scheduled_time,
        meeting_link=req.meeting_link,
    )
    return await resume_workflow(
        db=db,
        user_id=int(current_user.id),
        job_id=job_id,
        action="interview_invite",
        state_updates={"scheduled_interviews": interviews, "current_stage": "interviewing"},
    )


@router.post("/{job_id}/interview-complete")
async def interview_complete(
    job_id: str,
    req: InterviewCompletionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireHR],
):
    """HR action: record interview result and only progress when selected."""
    require_job_access(db, current_user, job_id)
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    state = status.get("state", {}) or {}

    assessments = state.get("interview_assessments", [])
    if not isinstance(assessments, list):
        assessments = []

    overall = (
        req.technical_score + req.communication_score + req.problem_solving_score + req.cultural_fit_score
    ) / 4.0
    assessment = Assessment(
        candidate_id=req.candidate_id,
        candidate_name=req.candidate_name,
        technical_score=req.technical_score,
        communication_score=req.communication_score,
        problem_solving_score=req.problem_solving_score,
        cultural_fit_score=req.cultural_fit_score,
        overall_score=overall,
        key_observations=req.observations,
        concerns=req.concerns,
        transcript_summary="HR recorded interview outcome.",
    ).model_dump(mode="json")
    assessments.append(assessment)

    updates: dict = {"interview_assessments": assessments}
    if req.selected:
        recommendations = state.get("final_recommendations", [])
        traces = state.get("decision_traces", [])
        if not isinstance(recommendations, list):
            recommendations = []
        if not isinstance(traces, list):
            traces = []
        weighted = round(overall * 10, 1)
        recommendations.append(
            Recommendation(
                candidate_id=req.candidate_id,
                candidate_name=req.candidate_name,
                decision="hire",
                confidence=weighted,
                screening_weight=0.0,
                interview_weight=weighted,
                overall_weighted_score=weighted,
                reasoning="Selected by HR after interview completion.",
                risk_factors=req.concerns,
            ).model_dump(mode="json")
        )
        traces.append(
            DecisionTrace(
                candidate_id=req.candidate_id,
                candidate_name=req.candidate_name,
                screening_score=0.0,
                interview_score_scaled=weighted,
                concerns_count=len(req.concerns),
                weighted_score=weighted,
                decision="hire",
                rule_applied="hr-selected-after-interview",
            ).model_dump(mode="json")
        )
        updates.update(
            {
                "final_recommendations": recommendations,
                "decision_traces": traces,
                "hire_approval": "pending",
                "current_stage": "hire_review",
            }
        )
    else:
        updates["current_stage"] = "interviewing"

    return await resume_workflow(
        db=db,
        user_id=int(current_user.id),
        job_id=job_id,
        action="interview_complete",
        state_updates=updates,
    )


@router.post("/{job_id}/generate-offer")
async def generate_offer(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireHR],
):
    """HR action: one-click offer generation for selected candidates."""
    require_job_access(db, current_user, job_id)
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    state = status.get("state", {}) or {}
    if state.get("current_stage") != "hire_review":
        raise HTTPException(status_code=400, detail="Offer generation is only available at hire_review stage")
    return await resume_workflow(
        db=db,
        user_id=int(current_user.id),
        job_id=job_id,
        action="approve",
        state_updates={"human_feedback": f"Offer generated by HR click @ {datetime.now().isoformat()}"},
    )


@router.post("/{job_id}/responses")
async def capture_response(
    job_id: str,
    req: CandidateResponseRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireHR],
):
    """Capture real candidate response payloads from an external communication flow."""
    try:
        require_job_access(db, current_user, job_id)
        return append_candidate_response(
            db=db,
            job_id=job_id,
            candidate_id=req.candidate_id,
            candidate_name=req.candidate_name,
            response_text=req.response,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/status")
async def get_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current pipeline stage for a job."""
    require_job_access(db, current_user, job_id)
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
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the full audit trail for a job."""
    require_job_access(db, current_user, job_id)
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
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get scheduled interviews and assessments for a job."""
    require_job_access(db, current_user, job_id)
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
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get final hire/no-hire recommendations for a job."""
    require_job_access(db, current_user, job_id)
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    state = status.get("state", {})
    return {
        "job_id": job_id,
        "final_recommendations": state.get("final_recommendations", []),
        "decision_traces": state.get("decision_traces", []),
    }
