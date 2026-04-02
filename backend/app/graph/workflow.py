"""Workflow engine for PRO HR.

Orchestrates 7 distinct agents using LangGraph to manage the
end-to-end recruitment lifecycle from JD intake to Offer.
"""

from __future__ import annotations

import json
import uuid
import logging
import asyncio
from datetime import datetime
from typing import TypedDict, Annotated, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.orm import Session

from app.models.state import RecruitmentState, PipelineStage
from app.models.db_models import Job, AuditEvent
from app.agents.jd_architect import create_jd_architect
from app.agents.liaison import create_liaison
from app.agents.scout import create_scout
from app.agents.screener import create_screener_single
from app.agents.coordinator import create_coordinator
from app.agents.outreach import create_outreach_agent
from app.agents.response_tracker import create_response_tracker

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: Stage Checkers (Logical Gates)
# ---------------------------------------------------------------------------

def check_jd_approval(state: RecruitmentState) -> Literal["approved", "rejected", "pending"]:
    approval = state.get("jd_approval", "pending")
    if approval == "approved":
        return "approved"
    elif approval == "rejected":
        return "rejected"
    return "pending"


def check_shortlist_approval(state: RecruitmentState) -> Literal["approved", "rejected", "pending"]:
    approval = state.get("shortlist_approval", "pending")
    if approval == "approved":
        return "approved"
    elif approval == "rejected":
        return "rejected"
    return "pending"


def check_hire_approval(state: RecruitmentState) -> Literal["approved", "rejected", "pending"]:
    approval = state.get("hire_approval", "pending")
    if approval == "approved":
        return "approved"
    elif approval == "rejected":
        return "rejected"
    return "pending"


def collect_scores(state: RecruitmentState) -> dict:
    """Consolidate scores from parallel screener nodes."""
    return {"current_stage": PipelineStage.SHORTLIST_REVIEW.value}


def _get_checkpointer():
    """In-memory checkpointer for session persistence."""
    return MemorySaver()


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_workflow_graph() -> StateGraph:
    """Build the full recruitment pipeline with 7 consolidated agents."""

    # Initialize Agent components
    jd_architect = create_jd_architect()
    liaison = create_liaison()
    scout = create_scout()
    screener_single = create_screener_single()
    coordinator = create_coordinator()
    outreach = create_outreach_agent()
    response_tracker = create_response_tracker()

    graph = StateGraph(RecruitmentState)

    # --- Nodes ---
    graph.add_node("jd_architect", jd_architect)
    graph.add_node("liaison_jd", liaison)
    graph.add_node("scout", scout)

    # Parallel scoring nodes
    graph.add_node("screener_single", screener_single)
    graph.add_node("collect_scores", collect_scores)

    graph.add_node("liaison_shortlist", liaison)
    graph.add_node("coordinator", coordinator)
    graph.add_node("liaison_hire", liaison)
    graph.add_node("outreach", outreach)
    graph.add_node("response_tracker", response_tracker)

    # --- Edges ---
    graph.set_entry_point("jd_architect")
    graph.add_edge("jd_architect", "liaison_jd")

    # JD approval gate
    graph.add_conditional_edges(
        "liaison_jd",
        check_jd_approval,
        {
            "approved": "scout",
            "rejected": "jd_architect",
            "pending": END,
        },
    )

    # Scout fans out to parallel screener_single nodes
    graph.add_edge("scout", "screener_single")
    graph.add_edge("screener_single", "collect_scores")
    graph.add_edge("collect_scores", "liaison_shortlist")

    # Shortlist approval gate
    graph.add_conditional_edges(
        "liaison_shortlist",
        check_shortlist_approval,
        {
            "approved": "liaison_hire",
            "rejected": "scout",
            "pending": END,
        },
    )

    # Final hire approval gate
    graph.add_conditional_edges(
        "liaison_hire",
        check_hire_approval,
        {
            "approved": "coordinator",
            "rejected": "scout",
            "pending": END,
        },
    )

    graph.add_edge("coordinator", "outreach")
    graph.add_edge("outreach", "response_tracker")
    graph.add_edge("response_tracker", END)

    return graph


# Compile once with persistent checkpointer
_checkpointer = _get_checkpointer()
_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_workflow_graph()
        _compiled_graph = graph.compile(checkpointer=_checkpointer)
    return _compiled_graph


# ---------------------------------------------------------------------------
# Workflow management
# ---------------------------------------------------------------------------

async def start_workflow(
    db: Session,
    user_id: int,
    job_title: str,
    department: str,
    requirements: list[str],
    preferred_qualifications: list[str] | None = None,
    location: str = "Remote",
    salary_range: str = "Competitive",
) -> dict:
    """Start a new recruitment workflow attached to a user."""
    job_id = str(uuid.uuid4())[:8]

    initial_state: RecruitmentState = {
        "job_id": job_id,
        "job_title": job_title,
        "department": department,
        "requirements": requirements,
        "preferred_qualifications": preferred_qualifications or [],
        "location": location,
        "salary_range": salary_range,
        "job_description": "",
        "jd_approval": "pending",
        "shortlist_approval": "pending",
        "hire_approval": "pending",
        "human_feedback": "",
        "candidates": [],
        "scored_candidates": [],
        "scheduled_interviews": [],
        "interview_assessments": [],
        "interview_transcripts": [],
        "final_recommendations": [],
        "current_stage": PipelineStage.JD_DRAFTING.value,
        "audit_log": [{
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "action": "workflow_started",
            "details": f"Pipeline started for {job_title} in {department}",
            "stage": PipelineStage.INTAKE.value,
        }],
        "error": "",
    }

    config = {"configurable": {"thread_id": job_id}}

    # 1. Create Database Record FIRST
    new_job = Job(
        job_id=job_id,
        job_title=job_title,
        department=department,
        location=location,
        salary_range=salary_range,
        requirements=requirements,
        preferred_qualifications=preferred_qualifications or [],
        current_stage=PipelineStage.JD_DRAFTING.value,
        created_by_id=user_id,
        workflow_state=initial_state
    )
    db.add(new_job)

    # Add initial audit event
    db.add(AuditEvent(
        job_id=job_id,
        agent="System",
        action="workflow_started",
        details=f"Pipeline started for {job_title} in {department}",
        stage=PipelineStage.INTAKE.value
    ))
    db.commit()

    # 2. Fire-and-forget graph invocation (background task)
    asyncio.create_task(_run_graph_task(db, job_id, initial_state, config))

    # Return immediately while Agent 01 (JD Architect) works in background
    logger.info(f"Workflow {job_id} initialized. Agent 01 (JD Architect) started in background.")
    return {
        "job_id": job_id,
        "status": "initializing",
        "current_stage": PipelineStage.JD_DRAFTING.value,
        "state": initial_state,
    }


async def _run_graph_task(db: Session, job_id: str, state: dict, config: dict):
    """Background task to execute the graph and sync state."""
    try:
        compiled = get_compiled_graph()
        result = await compiled.ainvoke(state, config=config)
        
        # We need a new session if the old one is closed by the caller
        from app.core.database import SessionLocal
        with SessionLocal() as new_db:
             job = new_db.query(Job).filter(Job.job_id == job_id).first()
             if job:
                 _sync_state_to_db(new_db, job, result)
                 new_db.commit()
        logger.info(f"Background workflow {job_id} sync complete.")
    except Exception as e:
        logger.error(f"Background workflow {job_id} failed: {e}", exc_info=True)


async def approve_stage(db: Session, job_id: str, feedback: str = "", updated_jd: str | None = None) -> dict:
    """Convenience wrapper for approving a stage."""
    # We need a user_id for resume_workflow (legacy requirement)
    # We'll fetch the owner of the job
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job: raise ValueError("Job not found")
    
    updates = {"human_feedback": feedback}
    if updated_jd:
        updates["job_description"] = updated_jd
        
    return await resume_workflow(db, job.created_by_id, job_id, "approve", updates)


async def reject_stage(db: Session, job_id: str, feedback: str) -> dict:
    """Convenience wrapper for rejecting a stage."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job: raise ValueError("Job not found")
    
    return await resume_workflow(db, job.created_by_id, job_id, "reject", {"human_feedback": feedback})


async def resume_workflow(
    db: Session,
    user_id: int,
    job_id: str,
    action: str,
    state_updates: dict | None = None,
) -> dict:
    """Resume a workflow after human intervention (approval/rejection)."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    config = {"configurable": {"thread_id": job_id}}
    state = job.workflow_state

    # Update state with human action
    if state_updates:
        for k, v in state_updates.items():
            state[k] = v

    if action == "approve":
        # Determine which approval flag to set
        if state["current_stage"] == PipelineStage.JD_REVIEW.value:
            state["jd_approval"] = "approved"
        elif state["current_stage"] == PipelineStage.SHORTLIST_REVIEW.value:
            state["shortlist_approval"] = "approved"
    elif action == "reject":
        if state["current_stage"] == PipelineStage.JD_REVIEW.value:
            state["jd_approval"] = "rejected"
            state["current_stage"] = PipelineStage.JD_DRAFTING.value
        elif state["current_stage"] == PipelineStage.SHORTLIST_REVIEW.value:
            state["shortlist_approval"] = "rejected"
            state["current_stage"] = PipelineStage.SOURCING.value

    # Resume graph execution from breakpoints
    compiled = get_compiled_graph()
    try:
        # We run this in foreground for now so the UI gets immediate feedback on the state change
        result = await compiled.ainvoke(None, config=config)
        _sync_state_to_db(db, job, result)
        db.commit()
        return result
    except Exception as e:
        logger.error(f"Failed to resume workflow {job_id}: {e}")
        raise


def get_workflow_status(db: Session, job_id: str) -> dict | None:
    """Fetch current status and state for a workflow."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        return None

    return {
        "job_id": job.job_id,
        "job_title": job.job_title,
        "department": job.department,
        "current_stage": job.current_stage,
        "state": job.workflow_state,
        "created_at": job.created_at.isoformat(),
    }


def get_all_workflows(db: Session) -> list[dict]:
    """Fetch all active workflows."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [{
        "job_id": j.job_id,
        "job_title": j.job_title,
        "department": j.department,
        "current_stage": j.current_stage,
        "created_at": j.created_at.isoformat(),
    } for j in jobs]


def _sync_state_to_db(db: Session, job: Job, state: RecruitmentState):
    """Update SQL model fields from the flattened RecruitmentState."""
    job.current_stage = state.get("current_stage", job.current_stage)
    job.workflow_state = state

    # Also log any new audit entries to the global AuditEvent table
    if "audit_log" in state:
        for entry in state["audit_log"]:
            existing = db.query(AuditEvent).filter(
                AuditEvent.job_id == job.job_id,
                AuditEvent.timestamp == entry["timestamp"]
            ).first()
            if not existing:
                db.add(AuditEvent(
                    job_id=job.job_id,
                    agent=entry["agent"],
                    action=entry["action"],
                    details=entry["details"],
                    stage=entry["stage"]
                ))
