import pytest
import asyncio

pytestmark = pytest.mark.integration

from unittest.mock import patch
from app.models.state import SharedState, PipelineStage
from app.core.orchestrator import Orchestrator
from app.models.db_models import Job

_TEST_TITLE = "Fault tolerance role"
_TEST_DEPT = "Engineering"


@pytest.mark.asyncio
async def test_error_resiliency(db):
    """Verify that an agent failure records the error but doesn't crash the orchestrator."""
    
    job_id = "error-test"
    state = SharedState(
        job_id=job_id,
        job_title=_TEST_TITLE,
        department=_TEST_DEPT,
        current_stage=PipelineStage.JD_DRAFTING.value,
    )
    job = Job(
        job_id=job_id,
        job_title=_TEST_TITLE,
        department=_TEST_DEPT,
        workflow_state=state.model_dump(mode="json"),
        current_stage=state.current_stage,
    )
    db.add(job)
    db.commit()
    
    with patch("app.core.orchestrator.jd_architect_node", side_effect=ValueError("Test Failure")):
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
    
    input_state_1 = SharedState(
        job_id="job1",
        job_title=_TEST_TITLE,
        department=_TEST_DEPT,
        current_stage=PipelineStage.JD_DRAFTING.value,
    )
    input_state_2 = SharedState(
        job_id="job2",
        job_title=_TEST_TITLE,
        department=_TEST_DEPT,
        current_stage=PipelineStage.JD_DRAFTING.value,
    )
    
    with patch("app.core.orchestrator.jd_architect_node") as mock_jd:
        mock_jd.return_value = SharedState(
            job_id="any",
            current_stage=PipelineStage.JD_REVIEW.value,
            job_description="Standardized JD Text.",
        )
        
        db.add(
            Job(
                job_id="job1",
                job_title=_TEST_TITLE,
                department=_TEST_DEPT,
                workflow_state=input_state_1.model_dump(mode="json"),
                current_stage=PipelineStage.JD_DRAFTING.value,
            )
        )
        db.add(
            Job(
                job_id="job2",
                job_title=_TEST_TITLE,
                department=_TEST_DEPT,
                workflow_state=input_state_2.model_dump(mode="json"),
                current_stage=PipelineStage.JD_DRAFTING.value,
            )
        )
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
        state = SharedState(
            job_id=jid,
            job_title=_TEST_TITLE,
            department=_TEST_DEPT,
            current_stage=PipelineStage.JD_DRAFTING.value,
        )
        db.add(
            Job(
                job_id=jid,
                job_title=_TEST_TITLE,
                department=_TEST_DEPT,
                workflow_state=state.model_dump(mode="json"),
                current_stage=state.current_stage,
            )
        )
    db.commit()
    
    with patch("app.core.orchestrator.jd_architect_node") as mock_jd:
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
