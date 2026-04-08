"""Analytics API — funnel, time-to-hire, score distribution, department breakdown."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.observability import snapshot as observability_snapshot
from app.models.db_models import Job, CandidateScore, Recommendation, AuditEvent, Outreach, Offer, User

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _auth(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


def _admin_only(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if str(current_user.role) != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.get("/funnel")
async def funnel(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Candidate hiring funnel: total sourced → screened → interviewed → hired."""
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    total_scored = db.query(func.count(CandidateScore.id)).scalar() or 0
    outreach_sent = db.query(func.count(Outreach.id)).scalar() or 0
    total_recommendations = db.query(func.count(Recommendation.id)).scalar() or 0
    offers_drafted = db.query(func.count(Offer.id)).scalar() or 0
    hired = (
        db.query(func.count(Recommendation.id))
        .filter(Recommendation.decision == "hire")
        .scalar() or 0
    )

    return {
        "funnel": [
            {"stage": "Pipelines Started", "count": total_jobs},
            {"stage": "Candidates Scored", "count": total_scored},
            {"stage": "Outreach Sent", "count": outreach_sent},
            {"stage": "Decisions Made", "count": total_recommendations},
            {"stage": "Offers Drafted", "count": offers_drafted},
            {"stage": "Hired", "count": hired},
        ]
    }


@router.get("/score_distribution")
async def score_distribution(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Histogram of candidate screening scores in buckets of 10."""
    scores = db.query(CandidateScore.overall_score).all()
    buckets: dict[str, int] = defaultdict(int)
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
    try:
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
    except Exception:
        logging.exception("Dept Breakdown Error")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


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
            try:
                days = (job.completed_at - job.created_at).total_seconds() / 86400
                by_dept[str(job.department or "Unknown")].append(days)
            except (TypeError, AttributeError):
                continue

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


@router.get("/roi/{job_id}")
async def job_roi(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Calculate ROI and Time Savings for a specific job pipeline."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    state: dict = dict(job.workflow_state or {})
    candidates_count = len(state.get("candidates", []))
    len(state.get("scored_candidates", []))
    interviews_count = len(state.get("scheduled_interviews", []))

    # ROI Formula (Industry benchmarks)
    # 15 mins per candidate screening
    # 60 mins per interview coordination + review
    # 30 mins for JD drafting
    manual_hours = (candidates_count * 0.25) + (interviews_count * 1.0) + 0.5
    ai_hours = 0.1 # Negligible (automated)
    
    hours_saved = max(0, manual_hours - ai_hours)
    monetary_roi = hours_saved * 80 # $80/hr benchmark

    return {
        "job_id": job_id,
        "metrics": {
            "candidates_processed": candidates_count,
            "interviews_automated": interviews_count,
            "manual_hours_estimated": round(manual_hours, 1),
            "hours_saved": round(hours_saved, 1),
            "monetary_roi": round(monetary_roi, 2),
            "efficiency_gain": "98%" if hours_saved > 0 else "0%"
        }
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


@router.get("/dashboard")
async def get_full_dashboard(
    db: Annotated[Session, Depends(get_db)],
    _=Depends(_auth),
):
    """Aggregated endpoint for the entire analytics dashboard."""
    try:
        # 1. Summary
        total_jobs = db.query(func.count(Job.id)).scalar() or 0
        active_jobs = db.query(func.count(Job.id)).filter(Job.current_stage != "completed").scalar() or 0
        total_candidates = db.query(func.count(CandidateScore.id)).scalar() or 0
        hired = db.query(func.count(Recommendation.id)).filter(Recommendation.decision == "hire").scalar() or 0
        avg_score = db.query(func.avg(CandidateScore.overall_score)).scalar()
        
        try:
            score_val = float(avg_score) if avg_score is not None else 0.0
        except (TypeError, ValueError):
            score_val = 0.0
        
        summary_data = {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "total_candidates_scored": total_candidates,
            "total_hires": hired,
            "average_screening_score": round(score_val, 1),
        }

        # 2. Funnel
        funnel_data = [
            {"stage": "Pipelines Started", "count": total_jobs},
            {"stage": "Candidates Scored", "count": total_candidates},
            {"stage": "Decisions Made", "count": db.query(func.count(Recommendation.id)).scalar() or 0},
            {"stage": "Hired", "count": hired},
        ]

        # 3. Time-to-Hire
        completed = db.query(Job).filter(Job.current_stage == "completed", Job.completed_at.isnot(None)).all()
        by_dept: dict[str, list[float]] = defaultdict(list)
        for job in completed:
            if job.created_at and job.completed_at:
                try:
                    days = (job.completed_at - job.created_at).total_seconds() / 86400
                    by_dept[str(job.department or "Unknown")].append(days)
                except (TypeError, AttributeError):
                    continue
        time_data = [
            {"department": dept, "avg_days": round(sum(days) / len(days), 1) if days else 0}
            for dept, days in by_dept.items()
        ]

        # 4. Recent Activity
        events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(15).all()
        recent_data = [
            {
                "agent": e.agent,
                "action": e.action,
                "details": e.details,
                "timestamp": e.timestamp.isoformat() if e.timestamp else "",
            }
            for e in events
        ]

        return {
            "summary": summary_data,
            "funnel": funnel_data,
            "time_to_hire": time_data,
            "recent": recent_data
        }
    except Exception:
        logging.exception("Dashboard Error")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


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

    try:
        score_val = float(avg_score) if avg_score is not None else 0.0
    except (TypeError, ValueError):
        score_val = 0.0

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_candidates_scored": total_candidates,
        "total_hires": hired,
        "pending_approvals": pending_approvals,
        "average_screening_score": round(score_val, 1),
    }


@router.get("/observability")
async def observability_metrics(
    _: Annotated[User, Depends(_admin_only)],
):
    """Lightweight in-memory operational counters (admin only)."""
    return {"observability": observability_snapshot()}


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics_text(
    _: Annotated[User, Depends(_admin_only)],
):
    """Prometheus-style text metrics for lightweight operational counters (admin only)."""
    metrics = observability_snapshot()
    duration_count = metrics.get("agent_duration_ms_count", 0)
    duration_sum = metrics.get("agent_duration_ms_sum", 0)
    avg_duration = (duration_sum / duration_count) if duration_count else 0.0
    lines = [
        "# HELP prohr_ws_ticket_issued_total Total number of WebSocket tickets issued.",
        "# TYPE prohr_ws_ticket_issued_total counter",
        f"prohr_ws_ticket_issued_total {metrics.get('ws_ticket_issued', 0)}",
        "# HELP prohr_ws_ticket_denied_total Total number of denied WebSocket ticket requests.",
        "# TYPE prohr_ws_ticket_denied_total counter",
        f"prohr_ws_ticket_denied_total {metrics.get('ws_ticket_denied', 0)}",
        "# HELP prohr_ws_connect_success_total Total successful WebSocket connections.",
        "# TYPE prohr_ws_connect_success_total counter",
        f"prohr_ws_connect_success_total {metrics.get('ws_connect_success', 0)}",
        "# HELP prohr_ws_connect_rejected_total Total rejected WebSocket connections.",
        "# TYPE prohr_ws_connect_rejected_total counter",
        f"prohr_ws_connect_rejected_total {metrics.get('ws_connect_rejected', 0)}",
        "# HELP prohr_agent_runs_success_total Total successful agent executions.",
        "# TYPE prohr_agent_runs_success_total counter",
        f"prohr_agent_runs_success_total {metrics.get('agent_runs_success', 0)}",
        "# HELP prohr_agent_runs_failed_total Total failed agent executions.",
        "# TYPE prohr_agent_runs_failed_total counter",
        f"prohr_agent_runs_failed_total {metrics.get('agent_runs_failed', 0)}",
        "# HELP prohr_agent_duration_ms_sum Sum of all agent durations in milliseconds.",
        "# TYPE prohr_agent_duration_ms_sum counter",
        f"prohr_agent_duration_ms_sum {duration_sum}",
        "# HELP prohr_agent_duration_ms_count Total count of measured agent durations.",
        "# TYPE prohr_agent_duration_ms_count counter",
        f"prohr_agent_duration_ms_count {duration_count}",
        "# HELP prohr_agent_duration_ms_avg Average agent duration in milliseconds.",
        "# TYPE prohr_agent_duration_ms_avg gauge",
        f"prohr_agent_duration_ms_avg {avg_duration:.2f}",
        "",
    ]
    return "\n".join(lines)
