import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.models.state import SharedState, PipelineStage, ApprovalStatus, CandidateProfile
from app.models.db_models import Job
from app.core.orchestrator import Orchestrator, start_workflow, resume_workflow

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
    """Test full approval flow: intake -> drafting -> review -> approved -> sourcing."""
    
    job_id = "full-test"
    # Starting from drafting
    result = await start_workflow(db, 1, "Staff Engineer", "Backend", ["Go", "Distributed Systems"])
    job_id = result["job_id"]
    db.commit()
    
    # Mocking agents to move state forward instantly
    with patch("app.agents.jd_architect.jd_architect_node") as mock_jd:
        mock_jd.return_value = SharedState(
            job_id=job_id, 
            current_stage=PipelineStage.JD_REVIEW.value,
            job_description="Perfect JD text."
        )
        
        # This will run drafting - ensure it doesn't hit OpenAI
        from app.core.orchestrator import _run_orchestration_task
        with patch("app.agents.jd_architect.jd_architect_node") as mock_jd_node:
            mock_jd_node.return_value = SharedState(
                job_id=job_id, 
                current_stage=PipelineStage.JD_REVIEW.value,
                job_description="Mocked JD"
            )
            await _run_orchestration_task(job_id)
        
        # Check if halted at JD_REVIEW
        db.expire_all()
        job = db.query(Job).filter(Job.job_id == job_id).first()
        assert job.current_stage == PipelineStage.JD_REVIEW.value
        
        # Perform HITL Approval
        with patch("app.agents.scout.scout_node") as mock_scout:
            mock_scout.return_value = SharedState(
                job_id=job_id,
                current_stage=PipelineStage.SCREENING.value,
                candidates=[CandidateProfile(name="Mock candidate")]
            )
            
            await resume_workflow(db, 1, job_id, "approve", {"human_feedback": "Looks good."})
            db.commit()
            
            # Wait for background task to move it to sourcing
            await asyncio.sleep(0.1) 
            
            # Re-fetch and verify next stage
            db.expire_all()
            job = db.query(Job).filter(Job.job_id == job_id).first()
            assert job.current_stage == PipelineStage.SCREENING.value
            assert job.workflow_state["jd_approval"] == "approved"
