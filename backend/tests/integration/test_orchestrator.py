import pytest

pytestmark = pytest.mark.integration

from unittest.mock import AsyncMock, patch
from app.models.state import (
    SharedState,
    PipelineStage,
    ApprovalStatus,
    CandidateProfile,
    ScoredCandidate,
    Assessment,
)
from app.models.db_models import Job
from app.core.orchestrator import Orchestrator, start_workflow, resume_workflow

VALID_JD = """## Role Summary
Build reliable backend systems at scale.

## Core Responsibilities
- Design distributed backend services.

## Required Qualifications
- Go
- Distributed Systems

## Preferred Qualifications
- Cloud infrastructure

## Compensation & Benefits
- Competitive package with benefits.

## Interview Process
- Recruiter screen
- System design interview

## Equal Opportunity Statement
We are an equal opportunity employer.
"""

@pytest.mark.asyncio
async def test_orchestrator_initialization(db):
    """Verify orchestrator correctly loads from DB."""
    
    # Setup - create job record manually
    job_id = "test-123"
    job = Job(
        job_id=job_id,
        job_title="Test Job",
        department="Engineering",
        workflow_state=SharedState(
            job_id=job_id, 
            job_title="Test Job",
            current_stage=PipelineStage.JD_DRAFTING.value
        ).model_dump(mode='json'),
        current_stage=PipelineStage.JD_DRAFTING.value
    )
    db.add(job)
    db.commit()
    
    orchestrator = Orchestrator(db, job_id)
    assert orchestrator.state.job_id == job_id
    assert orchestrator.state.current_stage == PipelineStage.JD_DRAFTING.value

@pytest.mark.asyncio
async def test_hitl_approval_halt(db):
    """Ensure orchestrator halts at HITL checkpoints."""
    
    job_id = "hitl-test"
    state = SharedState(
        job_id=job_id, 
        current_stage=PipelineStage.JD_REVIEW.value,
        jd_approval="pending"
    )
    
    job = Job(
        job_id=job_id, 
        job_title="HITL Job",
        department="HR",
        workflow_state=state.model_dump(mode='json'), 
        current_stage=state.current_stage
    )
    db.add(job)
    db.commit()
    
    orchestrator = Orchestrator(db, job_id)
    
    # Execute should halt at breakpoint
    with patch("app.agents.liaison.liaison_node") as mock_liaison:
        await orchestrator.execute()
        assert not mock_liaison.called
        assert orchestrator.state.current_stage == PipelineStage.JD_REVIEW.value

@pytest.mark.asyncio
async def test_resume_workflow_approval(db):
    """JD approve moves to sourcing; mocked scout/screener advance to shortlist HITL without LLM calls."""
    
    job_id = "full-test"
    # Starting from drafting
    result = await start_workflow(db, 1, "Staff Engineer", "Backend", ["Go", "Distributed Systems"])
    job_id = result["job_id"]
    db.commit()
    
    # Mocking agents to move state forward instantly (patch where orchestrator holds the reference)
    from app.core.orchestrator import _run_orchestration_task
    with patch("app.core.orchestrator.jd_architect_node") as mock_jd_node:
        mock_jd_node.return_value = SharedState(
            job_id=job_id,
            current_stage=PipelineStage.JD_REVIEW.value,
            job_description="Mocked JD",
        )
        await _run_orchestration_task(job_id)
        
        # Check if halted at JD_REVIEW
        db.expire_all()
        job = db.query(Job).filter(Job.job_id == job_id).first()
        assert job.current_stage == PipelineStage.JD_REVIEW.value
        
        with patch("app.core.orchestrator.scout_node") as mock_scout, patch(
            "app.core.orchestrator.screener_node"
        ) as mock_screener:
            mock_scout.return_value = SharedState(
                job_id=job_id,
                current_stage=PipelineStage.SCREENING.value,
                candidates=[CandidateProfile(name="Mock candidate")],
                jd_approval=ApprovalStatus.APPROVED.value,
            )
            mock_screener.return_value = SharedState(
                job_id=job_id,
                current_stage=PipelineStage.SHORTLIST_REVIEW.value,
                jd_approval=ApprovalStatus.APPROVED.value,
                shortlist_approval=ApprovalStatus.PENDING.value,
                candidates=[CandidateProfile(name="Mock candidate")],
            )
            with patch("app.core.orchestrator.start_orchestration", new_callable=AsyncMock):
                await resume_workflow(
                    db,
                    1,
                    job_id,
                    "approve",
                    {"human_feedback": "Looks good.", "job_description": VALID_JD},
                )
            db.commit()

            orch = Orchestrator(db, job_id)
            await orch.execute()

            db.expire_all()
            job = db.query(Job).filter(Job.job_id == job_id).first()
            assert job.current_stage == PipelineStage.SHORTLIST_REVIEW.value
            assert job.workflow_state["jd_approval"] == "approved"
            assert job.workflow_state["shortlist_approval"] == ApprovalStatus.PENDING.value


@pytest.mark.asyncio
async def test_pipeline_reaches_final_decision_stage(db):
    """Decision stage should produce recommendations and halt at HIRE_REVIEW."""
    job_id = "decision-test"
    state = SharedState(
        job_id=job_id,
        job_title="Senior Backend Engineer",
        department="Engineering",
        current_stage=PipelineStage.DECISION.value,
        jd_approval=ApprovalStatus.APPROVED.value,
        shortlist_approval=ApprovalStatus.APPROVED.value,
        scored_candidates=[
            ScoredCandidate(
                candidate_id="cand-1",
                candidate_name="Alice",
                overall_score=85.0,
                gaps=[],
            )
        ],
        interview_assessments=[
            Assessment(
                candidate_id="cand-1",
                candidate_name="Alice",
                technical_score=8.5,
                communication_score=8.0,
                problem_solving_score=8.5,
                cultural_fit_score=8.0,
                overall_score=8.25,
                concerns=[],
            )
        ],
    )
    job = Job(
        job_id=job_id,
        job_title=state.job_title,
        department=state.department,
        workflow_state=state.model_dump(mode="json"),
        current_stage=state.current_stage,
        created_by_id=1,
    )
    db.add(job)
    db.commit()

    orchestrator = Orchestrator(db, job_id)
    await orchestrator.execute()

    db.expire_all()
    saved_job = db.query(Job).filter(Job.job_id == job_id).first()
    assert saved_job is not None
    assert saved_job.current_stage == PipelineStage.HIRE_REVIEW.value

    saved_state = SharedState(**saved_job.workflow_state)
    assert len(saved_state.final_recommendations) == 1
    rec = saved_state.final_recommendations[0]
    assert rec.candidate_id == "cand-1"
    assert rec.decision == "hire"
    assert saved_state.hire_approval == ApprovalStatus.PENDING.value
