import pytest
from unittest.mock import patch

pytestmark = pytest.mark.e2e

from app.models.state import (
    SharedState, PipelineStage, ApprovalStatus, 
    CandidateProfile, Interview, Recommendation, OfferRecord
)
from app.core.orchestrator import start_workflow, resume_workflow, Orchestrator
from app.models.db_models import Job

VALID_JD = """## Role Summary
Lead applied research hiring with measurable outcomes.

## Core Responsibilities
- Drive core research delivery.

## Required Qualifications
- Deep Learning
- Publication Record

## Preferred Qualifications
- Leadership

## Compensation & Benefits
- Competitive compensation and benefits.

## Interview Process
- Recruiter round
- Technical round

## Equal Opportunity Statement
We are an equal opportunity employer.
"""

@pytest.mark.asyncio
async def test_e2e_successful_hiring_cycle(db, monkeypatch):
    """Full recruitment lifecycle. Clears OpenAI key so conftest's ``test-key`` does not call the API."""
    from app.config import settings

    monkeypatch.setattr(settings, "openai_api_key", "")

    # 1. INTAKE
    result = await start_workflow(
        db, 1, "Principal Researcher", "AI Labs", 
        ["Deep Learning", "Publication Record", "Leadership"]
    )
    job_id = result["job_id"]
    db.commit() # Ensure background/manual tasks can see this record
    
    # helper to fetch re-synced state
    def get_state():
        db.expire_all()
        job = db.query(Job).filter(Job.job_id == job_id).first()
        return SharedState(**job.workflow_state)

    # 2. DRAFTING (Auto)
    with patch("app.core.orchestrator.jd_architect_node") as mock_jd:
        mock_jd.return_value = SharedState(
            job_id=job_id, 
            current_stage=PipelineStage.JD_REVIEW.value,
            job_description="High-level JD content."
        )
        orchestrator = Orchestrator(db, job_id)
        await orchestrator.execute()
        
        state = get_state()
        assert state.current_stage == PipelineStage.JD_REVIEW.value
        assert state.jd_approval == ApprovalStatus.PENDING.value

    # 3. APPROVAL (HITL)
    with patch("app.core.orchestrator.scout_node") as mock_scout:
        mock_scout.return_value = SharedState(
            job_id=job_id,
            current_stage=PipelineStage.SCREENING.value,
            candidates=[CandidateProfile(name="Alice ML Expert")],
            jd_approval=ApprovalStatus.APPROVED.value,
        )
        await resume_workflow(
            db, 1, job_id, "approve", {"human_feedback": "Perfect JD.", "job_description": VALID_JD}
        )
        db.commit() # Ensure manual task can see approval
        
        orchestrator = Orchestrator(db, job_id)
        await orchestrator.execute()
        
        state = get_state()
        # It moves SOURCING -> SCREENING (Auto) -> SHORTLIST_REVIEW (HITL)
        assert state.current_stage == PipelineStage.SHORTLIST_REVIEW.value
        assert state.jd_approval == ApprovalStatus.APPROVED.value

    # 4. SHORTLIST APPROVAL (HITL) -> AUTOMATED SCHEDULING -> INTERVIEWING
    with patch("app.core.orchestrator.coordinator_node") as mock_coord:
        # Coordinator moves state to Interviewing
        mock_coord.return_value = SharedState(
            job_id=job_id,
            current_stage=PipelineStage.INTERVIEWING.value,
            scheduled_interviews=[Interview(id="int1", candidate_id="id1", candidate_name="Alice", interview_type="Technical")],
            jd_approval=ApprovalStatus.APPROVED.value,
            shortlist_approval=ApprovalStatus.APPROVED.value,
        )
        await resume_workflow(db, 1, job_id, "approve", {"human_feedback": "Proceed to interviews."})
        db.commit()
        
        orchestrator = Orchestrator(db, job_id)
        await orchestrator.execute()
        
        state = get_state()
        assert state.current_stage == PipelineStage.INTERVIEWING.value

    # 6. DECISION -> HIRE_REVIEW
    with patch("app.core.orchestrator.coordinator_node") as mock_decider:
        # Mocking coordination to move to decision and final review
        mock_decider.return_value = SharedState(
            job_id=job_id,
            current_stage=PipelineStage.HIRE_REVIEW.value,
            final_recommendations=[Recommendation(candidate_id="id1", candidate_name="Alice", decision="hire")],
            jd_approval=ApprovalStatus.APPROVED.value,
            shortlist_approval=ApprovalStatus.APPROVED.value,
        )
        orchestrator = Orchestrator(db, job_id)
        await orchestrator.execute()
        
        state = get_state()
        assert state.current_stage == PipelineStage.HIRE_REVIEW.value

    # 7. FINAL HIRE APPROVAL -> OFFER Generation
    with patch("app.core.orchestrator.coordinator_node") as mock_offer:
        mock_offer.return_value = SharedState(
            job_id=job_id,
            current_stage=PipelineStage.COMPLETED.value,
            offer_details=[OfferRecord(candidate_id="id1", candidate_name="Alice", status="draft")],
            jd_approval=ApprovalStatus.APPROVED.value,
            shortlist_approval=ApprovalStatus.APPROVED.value,
            hire_approval=ApprovalStatus.APPROVED.value,
        )
        await resume_workflow(db, 1, job_id, "approve", {"human_feedback": "Generate offer."})
        db.commit()
        
        # Manual execute to move from OFFER to COMPLETED
        orchestrator = Orchestrator(db, job_id)
        await orchestrator.execute()
        
        state = get_state()
        assert state.current_stage == PipelineStage.COMPLETED.value
        assert len(state.offer_details) == 1
        if state.audit_log:
            assert state.audit_log[-1].stage == PipelineStage.COMPLETED.value
