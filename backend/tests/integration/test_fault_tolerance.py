import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.models.state import SharedState, PipelineStage
from app.core.orchestrator import Orchestrator, _run_orchestration_task
from app.models.db_models import Job

@pytest.mark.asyncio
async def test_error_resiliency(db):
    """Verify that an agent failure records the error but doesn't crash the orchestrator."""
    
    job_id = "error-test"
    state = SharedState(job_id=job_id, current_stage=PipelineStage.JD_DRAFTING.value)
    job = Job(job_id=job_id, workflow_state=state.model_dump(mode='json'), current_stage=state.current_stage)
    db.add(job)
    db.commit()
    
    # Mocking jd_architect_node to raise an exception
    with patch("app.agents.jd_architect.jd_architect_node", side_effect=ValueError("Test Failure")):
        orchestrator = Orchestrator(db, job_id)
        await orchestrator.execute()
        
        # Verify error was captured
        db.expire_all()
        job = db.query(Job).filter(Job.job_id == job_id).first()
        assert "Test Failure" in job.workflow_state["error"]
        assert job.current_stage == PipelineStage.JD_DRAFTING.value

@pytest.mark.asyncio
async def test_determinism_consistency(db):
    """Verify that the same input state produced by an agent results in the same orchestrator decision."""
    
    # Use identical states for two different runs
    input_state_1 = SharedState(job_id="job1", current_stage=PipelineStage.JD_DRAFTING.value)
    input_state_2 = SharedState(job_id="job2", current_stage=PipelineStage.JD_DRAFTING.value)
    
    with patch("app.agents.jd_architect.jd_architect_node") as mock_jd:
        # Mocking deterministic output
        mock_jd.return_value = SharedState(
            job_id="any", 
            current_stage=PipelineStage.JD_REVIEW.value,
            job_description="Standardized JD Text."
        )
        
        # Register both jobs in DB
        db.add(Job(job_id="job1", workflow_state=input_state_1.model_dump(mode='json'), current_stage="intake"))
        db.add(Job(job_id="job2", workflow_state=input_state_2.model_dump(mode='json'), current_stage="intake"))
        db.commit()
        
        # Execute both
        await Orchestrator(db, "job1").execute()
        await Orchestrator(db, "job2").execute()
        
        db.expire_all()
        j1 = db.query(Job).filter(Job.job_id == "job1").first()
        j2 = db.query(Job).filter(Job.job_id == "job2").first()
        
        # Assertions for identical logic results
        assert j1.current_stage == j2.current_stage
        assert j1.workflow_state["job_description"] == j2.workflow_state["job_description"]

@pytest.mark.asyncio
async def test_concurrent_execution_safety(db):
    """Verify that multiple orchestrators can run across different jobs safely."""
    
    jobs = ["concurrent-1", "concurrent-2", "concurrent-3"]
    for jid in jobs:
        state = SharedState(job_id=jid, current_stage=PipelineStage.JD_DRAFTING.value)
        db.add(Job(job_id=jid, workflow_state=state.model_dump(mode='json'), current_stage=state.current_stage))
    db.commit()
    
    with patch("app.agents.jd_architect.jd_architect_node") as mock_jd:
        mock_jd.return_value = SharedState(
            job_id="any", 
            current_stage=PipelineStage.JD_REVIEW.value,
            job_description="Concurrent success."
        )
        
        # Run three orchestrators simultaneously
        await asyncio.gather(*[Orchestrator(db, jid).execute() for jid in jobs])
        
        db.expire_all()
        for jid in jobs:
             j = db.query(Job).filter(Job.job_id == jid).first()
             assert j.current_stage == PipelineStage.JD_REVIEW.value
