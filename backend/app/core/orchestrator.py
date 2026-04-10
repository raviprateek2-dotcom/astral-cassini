"""Custom Deterministic Orchestrator Engine for PRO HR.

Replaces LangGraph with a strict, controllable Python state machine.
"""

from __future__ import annotations

import logging
import uuid
import asyncio
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.state import SharedState, PipelineStage, CandidateResponse
from app.models.db_models import Job, AuditEvent
from app.core.observability import increment, record_agent_run
from app.config import settings

from app.agents.jd_architect import jd_architect_node
from app.agents.liaison import liaison_node
from app.agents.scout import scout_node
from app.agents.screener import screener_node
from app.agents.coordinator import coordinator_node
from app.agents.outreach import create_outreach_agent
from app.agents.response_tracker import create_response_tracker
from app.agents.offer_generator import create_offer_generator


logger = logging.getLogger(__name__)
_outreach_node = create_outreach_agent()
_response_tracker_node = create_response_tracker()
_offer_generator_node = create_offer_generator()
_running_jobs: set[str] = set()

REQUIRED_JD_SECTIONS = [
    "Role Summary",
    "Core Responsibilities",
    "Required Qualifications",
    "Preferred Qualifications",
    "Compensation & Benefits",
    "Interview Process",
    "Equal Opportunity Statement",
]


def _missing_jd_sections(jd_text: str) -> list[str]:
    content = jd_text.lower()
    missing: list[str] = []
    for section in REQUIRED_JD_SECTIONS:
        if section.lower() not in content:
            missing.append(section)
    return missing


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
        self.state: SharedState
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
                    self.state = await self._run_agent("jd_architect", jd_architect_node, self.state)
                
                elif current_stage == PipelineStage.JD_REVIEW.value:
                    self.state = await self._run_agent("liaison", liaison_node, self.state)
                    
                elif current_stage == PipelineStage.SOURCING.value:
                    self.state = await self._run_agent("scout", scout_node, self.state)
                    
                elif current_stage == PipelineStage.SCREENING.value:
                    self.state = await self._run_agent("screener", screener_node, self.state)
                    
                elif current_stage == PipelineStage.SHORTLIST_REVIEW.value:
                    self.state = await self._run_agent("liaison", liaison_node, self.state)

                elif current_stage == PipelineStage.OUTREACH.value:
                    self.state = await self._run_agent("outreach", _outreach_node, self.state)

                elif current_stage == PipelineStage.ENGAGEMENT.value:
                    self.state = await self._run_agent("response_tracker", _response_tracker_node, self.state)
                    
                # Coordinator consolidates SCHEDULING -> INTERVIEWING -> DECISION -> HIRE_REVIEW
                elif current_stage in (PipelineStage.SCHEDULING.value, 
                                       PipelineStage.INTERVIEWING.value, 
                                       PipelineStage.DECISION.value, 
                                       PipelineStage.HIRE_REVIEW.value):
                    if current_stage == PipelineStage.HIRE_REVIEW.value:
                         self.state = await self._run_agent("liaison", liaison_node, self.state)
                    else:
                         self.state = await self._run_agent("coordinator", coordinator_node, self.state)

                elif current_stage == PipelineStage.OFFER.value:
                    self.state = await self._run_agent("offer_generator", _offer_generator_node, self.state)
                
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

    async def _run_agent(self, name: str, node_fn, state: SharedState) -> SharedState:
        started = time.perf_counter()
        try:
            next_state = await node_fn(state)
            increment(f"agent_{name}_success")
            record_agent_run(True, (time.perf_counter() - started) * 1000)
            return next_state
        except Exception:
            increment(f"agent_{name}_failure")
            record_agent_run(False, (time.perf_counter() - started) * 1000)
            raise

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
        try:
            from app.api.websocket import schedule_pipeline_snapshot

            schedule_pipeline_snapshot(self.job_id)
        except Exception:
            logger.debug("WebSocket notify skipped for job %s", self.job_id, exc_info=True)


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
    """Launch orchestration in background unless already running for this job."""
    if job_id in _running_jobs:
        logger.info("orchestration already running for job_id=%s, skipping duplicate trigger", job_id)
        return False
    _running_jobs.add(job_id)
    asyncio.create_task(_run_orchestration_task(job_id))
    return True


async def _run_orchestration_task(job_id: str):
    from app.core.database import SessionLocal
    with SessionLocal() as db:
        try:
            _record_run_metadata(db, job_id, status="running")
            orchestrator = Orchestrator(db, job_id)
            await orchestrator.execute()
            _record_run_metadata(db, job_id, status="completed")
        except Exception as exc:
            logger.error("orchestration task failed for job_id=%s", job_id, exc_info=True)
            _record_run_metadata(db, job_id, status="failed", last_error=str(exc))
        finally:
            _running_jobs.discard(job_id)


async def resume_workflow(
    db: Session,
    user_id: int,
    job_id: str,
    action: str,
    state_updates: dict | None = None,
) -> dict:
    
    orchestrator = Orchestrator(db, job_id)
    state: SharedState = orchestrator.state
    
    if state_updates:
        for k, v in state_updates.items():
            setattr(state, k, v)
    if action == "manual_patch":
        state.log_audit(
            "Manual Override",
            "state_patch",
            f"Manual patch applied by user_id={user_id}. {state.human_feedback}".strip(),
            state.current_stage,
        )
            
    if action == "approve":
        if state.current_stage == PipelineStage.JD_REVIEW.value:
            candidate_jd = str(
                (state_updates or {}).get("job_description", state.job_description or "")
            )
            missing = _missing_jd_sections(candidate_jd)
            if missing:
                raise ValueError(
                    "JD approval blocked. Missing required sections: "
                    + ", ".join(missing)
                )
            state.jd_approval = "approved"
            state.current_stage = PipelineStage.SOURCING.value # Move forward
        elif state.current_stage == PipelineStage.SHORTLIST_REVIEW.value:
            state.shortlist_approval = "approved"
            state.current_stage = PipelineStage.OUTREACH.value
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
    if not job:
        raise ValueError("Job not found")
    owner_id = _require_job_owner_id(job)

    updates = {"human_feedback": feedback}
    if updated_jd:
        updates["job_description"] = updated_jd
        
    return await resume_workflow(db, owner_id, job_id, "approve", updates)


async def reject_stage(db: Session, job_id: str, feedback: str) -> dict:
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise ValueError("Job not found")
    owner_id = _require_job_owner_id(job)

    return await resume_workflow(db, owner_id, job_id, "reject", {"human_feedback": feedback})


def _require_job_owner_id(job: Job) -> int:
    owner_id = job.created_by_id
    if owner_id is None:
        raise ValueError("Job owner is missing")
    return int(owner_id)


def get_workflow_status(db: Session, job_id: str) -> dict | None:
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
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [{
        "job_id": j.job_id,
        "job_title": j.job_title,
        "department": j.department,
        "current_stage": j.current_stage,
        "created_at": j.created_at.isoformat(),
    } for j in jobs]


def append_candidate_response(
    db: Session,
    job_id: str,
    candidate_id: str,
    candidate_name: str,
    response_text: str,
) -> dict:
    orchestrator = Orchestrator(db, job_id)
    orchestrator.state.candidate_responses.append(
        CandidateResponse(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            response=response_text,
            engagement_level="High",
        )
    )
    orchestrator.state.log_audit(
        "Candidate Response Webhook",
        "response_captured",
        f"Captured response from {candidate_name}.",
        orchestrator.state.current_stage,
    )
    orchestrator._save_state()
    return orchestrator.state.model_dump(mode="json")


def run_retention_cleanup(db: Session) -> dict:
    deleted_completed = 0
    deleted_overflow = 0
    if settings.retention_enabled and settings.retention_days_completed_jobs > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days_completed_jobs)
        old_completed = (
            db.query(Job)
            .filter(Job.current_stage == PipelineStage.COMPLETED.value, Job.completed_at.isnot(None), Job.completed_at < cutoff)
            .all()
        )
        deleted_completed = len(old_completed)
        for job in old_completed:
            db.delete(job)
        db.commit()

    if settings.retention_max_jobs > 0:
        ordered_jobs = db.query(Job).order_by(Job.created_at.desc()).all()
        overflow = ordered_jobs[settings.retention_max_jobs :]
        deleted_overflow = len(overflow)
        for job in overflow:
            db.delete(job)
        db.commit()
    return {"deleted_completed": deleted_completed, "deleted_overflow": deleted_overflow}


def _record_run_metadata(db: Session, job_id: str, status: str, last_error: str | None = None) -> None:
    """Store lightweight orchestrator run metadata in workflow_state."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        return
    state = dict(job.workflow_state or {})
    run_state = dict(state.get("_orchestrator", {}))
    now_iso = datetime.now(timezone.utc).isoformat()
    if status == "running":
        run_state["started_at"] = now_iso
    run_state["status"] = status
    run_state["updated_at"] = now_iso
    if status in {"completed", "failed"}:
        run_state["finished_at"] = now_iso
    if last_error:
        run_state["last_error"] = last_error
    state["_orchestrator"] = run_state
    setattr(job, "workflow_state", state)
    db.commit()
