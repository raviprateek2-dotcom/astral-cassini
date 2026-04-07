"""Custom Deterministic Orchestrator Engine for PRO HR.

Replaces LangGraph with a strict, controllable Python state machine.
"""

from __future__ import annotations

import logging
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.state import SharedState, PipelineStage
from app.models.db_models import Job, AuditEvent

from app.agents.jd_architect import jd_architect_node
from app.agents.liaison import liaison_node
from app.agents.scout import scout_node
from app.agents.screener import screener_node
from app.agents.coordinator import coordinator_node


logger = logging.getLogger(__name__)


class Orchestrator:
    """Manages execution flow of the recruitment pipeline deterministically."""
    
    def __init__(self, db: Session, job_id: str):
        self.db = db
        self.job_id = job_id
        
        # Load state from DB
        self.job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if not self.job:
            raise ValueError(f"Job {job_id} not found in DB.")
            
        # Parse Pydantic state
        if isinstance(self.job.workflow_state, dict):
            self.state = SharedState(**self.job.workflow_state)
        elif isinstance(self.job.workflow_state, SharedState):
            self.state = self.job.workflow_state
        else:
            self.state = SharedState(job_id=job_id)

    async def execute(self):
        """Run the pipeline until a natural halt or completion."""
        max_steps = 20
        steps = 0
        
        while steps < max_steps:
            current_stage = self.state.current_stage
            
            # Hit Breakpoints (HITL)
            if self._is_at_breakpoint():
                logger.info(f"Orchestrator halting at HITL breakpoint: {current_stage}")
                break
                
            if current_stage == PipelineStage.COMPLETED.value:
                logger.info("Pipeline Complete.")
                break
            # Node execution routing
            try:
                if current_stage == PipelineStage.JD_DRAFTING.value:
                    self.state = await jd_architect_node(self.state)
                
                elif current_stage == PipelineStage.JD_REVIEW.value:
                    self.state = await liaison_node(self.state)
                    
                elif current_stage == PipelineStage.SOURCING.value:
                    self.state = await scout_node(self.state)
                    
                elif current_stage == PipelineStage.SCREENING.value:
                    self.state = await screener_node(self.state)
                    
                elif current_stage == PipelineStage.SHORTLIST_REVIEW.value:
                    self.state = await liaison_node(self.state)
                    
                # Coordinator consolidates SCHEDULING -> INTERVIEWING -> DECISION -> HIRE_REVIEW -> OFFER
                elif current_stage in (PipelineStage.SCHEDULING.value, 
                                       PipelineStage.INTERVIEWING.value, 
                                       PipelineStage.DECISION.value, 
                                       PipelineStage.HIRE_REVIEW.value, 
                                       PipelineStage.OFFER.value):
                    if current_stage == PipelineStage.HIRE_REVIEW.value:
                         self.state = await liaison_node(self.state)
                    else:
                         self.state = await coordinator_node(self.state)
                
                else:
                    logger.warning(f"Unknown stage {current_stage}. Halting.")
                    break
                    
                # Commit state incrementally
                self._save_state()
                steps += 1
                
            except Exception as e:
                logger.error(f"Execution failed at {current_stage}: {str(e)}", exc_info=True)
                self.state.error = str(e)
                self._save_state()
                break

    def _is_at_breakpoint(self) -> bool:
        """Check if we are waiting for human approval."""
        if self.state.current_stage == PipelineStage.JD_REVIEW.value and self.state.jd_approval == "pending":
            return True
        if self.state.current_stage == PipelineStage.SHORTLIST_REVIEW.value and self.state.shortlist_approval == "pending":
            return True
        if self.state.current_stage == PipelineStage.HIRE_REVIEW.value and self.state.hire_approval == "pending":
            return True
        return False

    def _save_state(self):
        """Save Pydantic state directly into the SQLAlchemy DB."""
        self.job.current_stage = self.state.current_stage
        self.job.workflow_state = self.state.model_dump(mode='json')
        
        # Sync Audit Log
        for entry in self.state.audit_log:
            existing = self.db.query(AuditEvent).filter(
                AuditEvent.job_id == self.job.job_id,
                AuditEvent.timestamp == entry.timestamp
            ).first()
            if not existing:
                self.db.add(AuditEvent(
                    job_id=self.job.job_id,
                    agent=entry.agent,
                    action=entry.action,
                    details=entry.details,
                    stage=entry.stage
                ))
                
        self.db.commit()


# ---------------------------------------------------------------------------
# Public Workflow API (Replaces graph exports)
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
    
    job_id = str(uuid.uuid4())[:8]
    
    state = SharedState(
        job_id=job_id,
        job_title=job_title,
        department=department,
        requirements=requirements,
        preferred_qualifications=preferred_qualifications or [],
        location=location,
        salary_range=salary_range,
        current_stage=PipelineStage.JD_DRAFTING.value,
    )
    
    state.log_audit("System", "workflow_started", f"Pipeline started for {job_title}", PipelineStage.INTAKE.value)
    
    # 1. Create DB Record
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
        workflow_state=state.model_dump(mode='json')
    )
    db.add(new_job)
    db.commit()
    
    # 2. Fire and forget graph execution
    start_orchestration(job_id)
    
    return {
        "job_id": job_id,
        "status": "initializing",
        "current_stage": PipelineStage.JD_DRAFTING.value,
        "state": state.model_dump(mode='json'),
    }


def start_orchestration(job_id: str):
    """Launch the orchestration logic in a background task."""
    asyncio.create_task(_run_orchestration_task(job_id))


async def _run_orchestration_task(job_id: str):
    from app.core.database import SessionLocal
    with SessionLocal() as db:
        orchestrator = Orchestrator(db, job_id)
        await orchestrator.execute()


async def resume_workflow(
    db: Session,
    user_id: int,
    job_id: str,
    action: str,
    state_updates: dict | None = None,
) -> dict:
    
    orchestrator = Orchestrator(db, job_id)
    state = orchestrator.state
    
    if state_updates:
        for k, v in state_updates.items():
            setattr(state, k, v)
            
    if action == "approve":
        if state.current_stage == PipelineStage.JD_REVIEW.value:
            state.jd_approval = "approved"
            state.current_stage = PipelineStage.SOURCING.value # Move forward
        elif state.current_stage == PipelineStage.SHORTLIST_REVIEW.value:
            state.shortlist_approval = "approved"
            state.current_stage = PipelineStage.SCHEDULING.value
        elif state.current_stage == PipelineStage.HIRE_REVIEW.value:
             state.hire_approval = "approved"
             state.current_stage = PipelineStage.OFFER.value
             
    elif action == "reject":
        if state.current_stage == PipelineStage.JD_REVIEW.value:
            state.jd_approval = "rejected"
            state.current_stage = PipelineStage.JD_DRAFTING.value
        elif state.current_stage == PipelineStage.SHORTLIST_REVIEW.value:
            state.shortlist_approval = "rejected"
            state.current_stage = PipelineStage.SOURCING.value
        elif state.current_stage == PipelineStage.HIRE_REVIEW.value:
             state.hire_approval = "rejected"
             state.current_stage = PipelineStage.DECISION.value

    orchestrator._save_state()
    
    # Resume background
    start_orchestration(job_id)
    
    return orchestrator.state.model_dump(mode='json')


async def approve_stage(db: Session, job_id: str, feedback: str = "", updated_jd: str | None = None) -> dict:
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job: raise ValueError("Job not found")
    
    updates = {"human_feedback": feedback}
    if updated_jd:
        updates["job_description"] = updated_jd
        
    return await resume_workflow(db, job.created_by_id, job_id, "approve", updates)


async def reject_stage(db: Session, job_id: str, feedback: str) -> dict:
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job: raise ValueError("Job not found")
    
    return await resume_workflow(db, job.created_by_id, job_id, "reject", {"human_feedback": feedback})


def get_workflow_status(db: Session, job_id: str) -> dict | None:
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job: return None
    return {
        "job_id": job.job_id,
        "job_title": job.job_title,
        "department": job.department,
        "current_stage": job.current_stage,
        "state": job.workflow_state,
        "created_at": job.created_at.isoformat(),
    }


def get_all_workflows(db: Session) -> list[dict]:
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [{
        "job_id": j.job_id,
        "job_title": j.job_title,
        "department": j.department,
        "current_stage": j.current_stage,
        "created_at": j.created_at.isoformat(),
    } for j in jobs]
