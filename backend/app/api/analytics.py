"""Analytics API — funnel, time-to-hire, score distribution, department breakdown."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.db_models import Job, CandidateScore, Recommendation, AuditEvent, User

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _auth(current_user=Depends(get_current_user)):
    return current_user


@router.get("/funnel")
async def funnel(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Candidate hiring funnel: total sourced → screened → interviewed → hired."""
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    total_scored = db.query(func.count(CandidateScore.id)).scalar() or 0
    total_recommendations = db.query(func.count(Recommendation.id)).scalar() or 0
    hired = (
        db.query(func.count(Recommendation.id))
        .filter(Recommendation.decision == "hire")
        .scalar() or 0
    )
    maybe = (
        db.query(func.count(Recommendation.id))
        .filter(Recommendation.decision == "maybe")
        .scalar() or 0
    )

    return {
        "funnel": [
            {"stage": "Pipelines Started", "count": total_jobs},
            {"stage": "Candidates Scored", "count": total_scored},
            {"stage": "Decisions Made", "count": total_recommendations},
            {"stage": "Hire", "count": hired},
            {"stage": "Maybe", "count": maybe},
        ]
    }


@router.get("/score_distribution")
async def score_distribution(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Histogram of candidate screening scores in buckets of 10."""
    scores = db.query(CandidateScore.overall_score).all()
    buckets = defaultdict(int)
    for (score,) in scores:
        bucket = int(score // 10) * 10
        bucket = min(bucket, 90)
        buckets[f"{bucket}-{bucket+9}"] += 1

    labels = [f"{i}-{i+9}" for i in range(0, 100, 10)]
    return {
        "distribution": [
            {"range": label, "count": buckets.get(label, 0)}
            for label in labels
        ]
    }


@router.get("/department_breakdown")
async def department_breakdown(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Jobs and hires by department."""
    jobs = db.query(Job.department, func.count(Job.id)).group_by(Job.department).all()
    hires_raw = (
        db.query(Job.department, func.count(Recommendation.id))
        .join(Recommendation, Recommendation.job_id == Job.job_id)
        .filter(Recommendation.decision == "hire")
        .group_by(Job.department)
        .all()
    )
    hires_map = {dept: count for dept, count in hires_raw}
    return {
        "departments": [
            {
                "department": dept or "Unknown",
                "total_jobs": count,
                "hires": hires_map.get(dept, 0),
            }
            for dept, count in jobs
        ]
    }


@router.get("/time_to_hire")
async def time_to_hire(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Average time-to-complete (days) for finished pipelines, by department."""
    completed = (
        db.query(Job)
        .filter(Job.current_stage == "completed", Job.completed_at.isnot(None))
        .all()
    )
    by_dept: dict[str, list[float]] = defaultdict(list)
    for job in completed:
        if job.created_at and job.completed_at:
            days = (job.completed_at - job.created_at).total_seconds() / 86400
            by_dept[job.department or "Unknown"].append(days)

    return {
        "time_to_hire": [
            {
                "department": dept,
                "avg_days": round(sum(days) / len(days), 1) if days else 0,
                "count": len(days),
            }
            for dept, days in by_dept.items()
        ]
    }


@router.get("/recent_activity")
async def recent_activity(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Last 20 audit events across all pipelines."""
    events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.timestamp.desc())
        .limit(20)
        .all()
    )
    return {
        "events": [
            {
                "job_id": e.job_id,
                "agent": e.agent,
                "action": e.action,
                "details": e.details,
                "stage": e.stage,
                "timestamp": e.timestamp.isoformat() if e.timestamp else "",
            }
            for e in events
        ]
    }


@router.get("/summary")
async def summary(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Top-level KPIs for the dashboard."""
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    active_jobs = (
        db.query(func.count(Job.id))
        .filter(Job.current_stage != "completed")
        .scalar() or 0
    )
    total_candidates = db.query(func.count(CandidateScore.id)).scalar() or 0
    hired = (
        db.query(func.count(Recommendation.id))
        .filter(Recommendation.decision == "hire")
        .scalar() or 0
    )
    pending_approvals = (
        db.query(func.count(Job.id))
        .filter(Job.current_stage.in_(["jd_review", "shortlist_review", "hire_review"]))
        .scalar() or 0
    )
    avg_score = (
        db.query(func.avg(CandidateScore.overall_score)).scalar()
    )

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_candidates_scored": total_candidates,
        "total_hires": hired,
        "pending_approvals": pending_approvals,
        "average_screening_score": round(float(avg_score), 1) if avg_score else 0.0,
    }
