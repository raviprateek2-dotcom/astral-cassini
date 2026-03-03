"""Improved LangGraph Workflow — Full recruitment pipeline orchestration.

Key improvements over v1:
1. SqliteSaver checkpointer — workflows survive server restarts
2. Parallel candidate scoring via LangGraph's Send API
3. Streaming-ready async graph execution
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Annotated

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.db_models import Job, CandidateScore, Interview, AuditEvent, Recommendation
from app.models.state import RecruitmentState, PipelineStage
from app.agents.jd_architect import create_jd_architect
from app.agents.liaison import (
    create_liaison,
    check_jd_approval,
    check_shortlist_approval,
    check_hire_approval,
)
from app.agents.scout import create_scout
from app.agents.screener import create_screener_single   # NEW: scores ONE candidate
from app.agents.coordinator import create_coordinator
from app.agents.interviewer import create_interviewer
from app.agents.decider import create_decider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persistent SqliteSaver checkpointer
# ---------------------------------------------------------------------------

def _get_checkpointer():
    """Return a MemorySaver (SqliteSaver requires langgraph-checkpoint-sqlite)."""
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        import os
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/workflows.db", check_same_thread=False)
        saver = SqliteSaver(conn)
        logger.info("Using SqliteSaver — workflows will persist across restarts.")
        return saver
    except ImportError:
        logger.warning("SqliteSaver not available, using MemorySaver (in-memory only).")
        return MemorySaver()


# ---------------------------------------------------------------------------
# Parallel scoring dispatcher (LangGraph Send API)
# ---------------------------------------------------------------------------

def dispatch_scoring(state: RecruitmentState) -> list[Send]:
    """Fan-out: send each candidate to the screener_single node in parallel."""
    candidates = state.get("candidates", [])
    if not candidates:
        return []

    return [
        Send("screener_single", {
            "candidate": candidate,
            "job_description": state.get("job_description", ""),
            "requirements": state.get("requirements", []),
            "job_title": state.get("job_title", ""),
        })
        for candidate in candidates
    ]


def collect_scores(state: RecruitmentState) -> dict:
    """Fan-in: merge all individual scored_candidates into state."""
    # scored_candidates is already accumulated via the reducer (list append)
    scored = state.get("scored_candidates", [])
    # Sort by overall_score descending
    scored_sorted = sorted(scored, key=lambda x: x.get("overall_score", 0), reverse=True)

    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": "The Screener",
        "action": "parallel_scoring_complete",
        "details": f"Scored {len(scored_sorted)} candidates in parallel. Top: {scored_sorted[0].get('overall_score', 0):.1f}" if scored_sorted else "No candidates scored",
        "stage": PipelineStage.SCREENING.value,
    }

    return {
        "scored_candidates": scored_sorted,
        "current_stage": PipelineStage.SHORTLIST_REVIEW.value,
        "shortlist_approval": "pending",
        "audit_log": [audit_entry],
    }


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_workflow_graph() -> StateGraph:
    """Build the full recruitment pipeline with parallel scoring."""

    jd_architect = create_jd_architect()
    liaison = create_liaison()
    scout = create_scout()
    screener_single = create_screener_single()   # scores ONE candidate
    coordinator = create_coordinator()
    interviewer = create_interviewer()
    decider = create_decider()

    graph = StateGraph(RecruitmentState)

    # --- Nodes ---
    graph.add_node("jd_architect", jd_architect)
    graph.add_node("liaison_jd", liaison)
    graph.add_node("scout", scout)

    # Parallel scoring nodes
    graph.add_node("screener_single", screener_single)   # runs N times in parallel
    graph.add_node("collect_scores", collect_scores)     # fan-in aggregator

    graph.add_node("liaison_shortlist", liaison)
    graph.add_node("coordinator", coordinator)
    graph.add_node("interviewer", interviewer)
    graph.add_node("decider", decider)
    graph.add_node("liaison_hire", liaison)

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
    graph.add_conditional_edges(
        "scout",
        dispatch_scoring,
    )

    # Screener fan-in → collect_scores
    graph.add_edge("screener_single", "collect_scores")
    graph.add_edge("collect_scores", "liaison_shortlist")

    # Shortlist gate
    graph.add_conditional_edges(
        "liaison_shortlist",
        check_shortlist_approval,
        {
            "approved": "coordinator",
            "rejected": "scout",
            "pending": END,
        },
    )

    graph.add_edge("coordinator", "interviewer")
    graph.add_edge("interviewer", "decider")
    graph.add_edge("decider", "liaison_hire")

    # Hire gate
    graph.add_conditional_edges(
        "liaison_hire",
        check_hire_approval,
        {
            "approved": END,
            "rejected": "scout",
            "pending": END,
        },
    )

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

    # 2. Invoke Graph
    try:
        compiled = get_compiled_graph()
        result = await compiled.ainvoke(initial_state, config=config)

        # Sync result to DB
        _sync_state_to_db(db, new_job, result)
        db.commit()

        logger.info(f"Workflow {job_id} started. Stage: {new_job.current_stage}")
        return {
            "job_id": job_id,
            "status": "running",
            "current_stage": new_job.current_stage,
            "state": result,
        }

    except Exception as e:
        logger.error(f"Failed to start workflow {job_id}: {e}", exc_info=True)
        initial_state["error"] = str(e)
        _sync_state_to_db(db, new_job, initial_state)
        db.commit()

        return {
            "job_id": job_id,
            "status": "error",
            "error": str(e),
            "current_stage": PipelineStage.JD_DRAFTING.value,
            "state": initial_state,
        }


def _sync_state_to_db(db: Session, job: Job, state: dict):
    """Sync the LangGraph state JSON into individual SQLAlchemy records for analytics."""
    job.workflow_state = state
    job.current_stage = state.get("current_stage", "unknown")
    job.jd_approval = state.get("jd_approval", "pending")
    job.shortlist_approval = state.get("shortlist_approval", "pending")
    job.hire_approval = state.get("hire_approval", "pending")
    if job.current_stage == PipelineStage.COMPLETED.value and not job.completed_at:
        job.completed_at = datetime.utcnow()

    # Sync Audit Logs
    for entry in state.get("audit_log", []):
        exists = db.query(AuditEvent).filter_by(
            job_id=job.job_id, timestamp=datetime.fromisoformat(entry["timestamp"]), action=entry.get("action")
        ).first()
        if not exists:
            db.add(AuditEvent(
                job_id=job.job_id,
                agent=entry.get("agent", "System"),
                action=entry.get("action", ""),
                details=entry.get("details", ""),
                stage=entry.get("stage", ""),
                timestamp=datetime.fromisoformat(entry["timestamp"])
            ))

    # Sync Candidate Scores (only once per candidate)
    for c in state.get("scored_candidates", []):
        exists = db.query(CandidateScore).filter_by(job_id=job.job_id, candidate_id=c["id"]).first()
        if not exists:
            db.add(CandidateScore(
                job_id=job.job_id, candidate_id=c["id"], candidate_name=c["name"],
                overall_score=c.get("overall_score", 0), skills_match=c.get("skills_match", 0),
                experience_match=c.get("experience_match", 0), education_match=c.get("education_match", 0),
                cultural_fit=c.get("cultural_fit", 0), strengths=c.get("strengths", []),
                gaps=c.get("gaps", []), reasoning=c.get("reasoning", "")
            ))

    # Sync Recommendations
    for r in state.get("final_recommendations", []):
        exists = db.query(Recommendation).filter_by(job_id=job.job_id, candidate_id=r["candidate_id"]).first()
        if not exists:
            db.add(Recommendation(
                job_id=job.job_id, candidate_id=r["candidate_id"], candidate_name=r["candidate_name"],
                decision=r.get("decision", "maybe"), confidence=r.get("confidence", 0),
                overall_weighted_score=r.get("overall_weighted_score", 0),
                screening_weight=r.get("screening_weight", 0), interview_weight=r.get("interview_weight", 0),
                reasoning=r.get("reasoning", ""), risk_factors=r.get("risk_factors", [])
            ))


async def _resume_workflow(db: Session, job: Job, updated_state: dict) -> dict:
    """Internal: resume a paused workflow with updated state."""
    config = {"configurable": {"thread_id": job.job_id}}
    try:
        compiled = get_compiled_graph()
        result = await compiled.ainvoke(updated_state, config=config)
        
        # Save to database
        _sync_state_to_db(db, job, result)
        db.commit()

        return {
            "job_id": job.job_id,
            "status": "running",
            "current_stage": result.get("current_stage", "unknown"),
            "state": result,
        }
    except Exception as e:
        logger.error(f"Failed to resume workflow {job.job_id}: {e}", exc_info=True)
        return {"job_id": job.job_id, "status": "error", "error": str(e)}


async def approve_stage(db: Session, job_id: str, feedback: str = "") -> dict:
    """Approve the current HITL gate and resume the workflow."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        return {"error": f"Workflow {job_id} not found"}
 
    state = job.workflow_state
    current_stage = state.get("current_stage", "")
 
    update: dict = {"human_feedback": feedback}
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": "Human Reviewer",
        "stage": current_stage,
    }
 
    stage_map = {
        PipelineStage.JD_REVIEW.value: ("jd_approval", PipelineStage.SOURCING.value, "jd_approved"),
        PipelineStage.SHORTLIST_REVIEW.value: ("shortlist_approval", PipelineStage.SCHEDULING.value, "shortlist_approved"),
        PipelineStage.HIRE_REVIEW.value: ("hire_approval", PipelineStage.COMPLETED.value, "hire_approved"),
    }
 
    if current_stage not in stage_map:
        return {"error": f"No pending approval at stage: {current_stage}"}
 
    approval_key, next_stage, action = stage_map[current_stage]
    update[approval_key] = "approved"
    update["current_stage"] = next_stage
    audit_entry["action"] = action
    audit_entry["details"] = f"Approved. Feedback: {feedback or 'None'}"
    update["audit_log"] = state.get("audit_log", []) + [audit_entry]
 
    return await _resume_workflow(db, job, {**state, **update})


async def reject_stage(db: Session, job_id: str, feedback: str) -> dict:
    """Reject the current HITL gate with required feedback."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        return {"error": f"Workflow {job_id} not found"}
 
    state = job.workflow_state
    current_stage = state.get("current_stage", "")
 
    update: dict = {"human_feedback": feedback}
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": "Human Reviewer",
        "stage": current_stage,
    }
 
    stage_map = {
        PipelineStage.JD_REVIEW.value: ("jd_approval", PipelineStage.JD_DRAFTING.value, "jd_rejected"),
        PipelineStage.SHORTLIST_REVIEW.value: ("shortlist_approval", PipelineStage.SOURCING.value, "shortlist_rejected"),
        PipelineStage.HIRE_REVIEW.value: ("hire_approval", PipelineStage.SOURCING.value, "hire_rejected"),
    }
 
    if current_stage not in stage_map:
        return {"error": f"No pending approval at stage: {current_stage}"}
 
    approval_key, next_stage, action = stage_map[current_stage]
    update[approval_key] = "rejected"
    update["current_stage"] = next_stage
    audit_entry["action"] = action
    audit_entry["details"] = f"Rejected. Feedback: {feedback}"
    update["audit_log"] = state.get("audit_log", []) + [audit_entry]
 
    return await _resume_workflow(db, job, {**state, **update})


async def resume_workflow(
    db: Session,
    user_id: int,
    job_id: str,
    action: str,
    state_updates: dict
) -> dict:
    """External entry point to update state and resume/trigger a workflow."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    current_state = job.workflow_state
    
    # Merge updates
    new_state = {**current_state, **state_updates}
    
    # Add audit event
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": "System (API)",
        "action": action,
        "details": f"External action triggered: {action}",
        "stage": new_state.get("current_stage", "unknown"),
    }
    new_state["audit_log"] = current_state.get("audit_log", []) + [audit_entry]
    
    # Sync basic info back if needed (candidates count etc)
    result = await _resume_workflow(db, job, new_state)
    return result.get("state", result)


def get_workflow_status(db: Session, job_id: str) -> dict | None:
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        return None
    state = job.workflow_state
    return {
        "job_id": job_id,
        "current_stage": state.get("current_stage", "unknown"),
        "job_title": state.get("job_title", ""),
        "department": state.get("department", ""),
        "created_at": str(job.created_at),
        "state": state,
    }


def get_all_workflows(db: Session) -> list[dict]:
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [
        {
            "job_id": j.job_id,
            "job_title": j.job_title,
            "department": j.department,
            "current_stage": j.current_stage,
            "candidates_count": len(j.workflow_state.get("candidates", [])),
            "created_at": str(j.created_at),
        }
        for j in jobs
    ]
