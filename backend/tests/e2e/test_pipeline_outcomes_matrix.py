"""Outcome matrix for pipeline gate decisions.

Validates approve/reject transitions at every HITL checkpoint:
- JD_REVIEW
- SHORTLIST_REVIEW
- HIRE_REVIEW
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.e2e

from app.config import settings
from app.core.orchestrator import Orchestrator, resume_workflow, start_workflow
from app.models.db_models import Job
from app.models.state import ApprovalStatus, PipelineStage, SharedState


async def _seed_job_at_jd_review(db, monkeypatch) -> str:
    """Create a job and halt it at JD_REVIEW pending."""
    monkeypatch.setattr(settings, "openai_api_key", "")

    async def fast_jd(state: SharedState) -> SharedState:
        return SharedState(
            **{
                **state.model_dump(),
                "job_description": "Mock JD",
                "current_stage": PipelineStage.JD_REVIEW.value,
                "jd_approval": ApprovalStatus.PENDING.value,
            }
        )

    result = await start_workflow(
        db,
        1,
        "Outcome Matrix Role",
        "QA",
        ["Python", "Testing"],
    )
    job_id = result["job_id"]
    db.commit()

    with patch("app.core.orchestrator.jd_architect_node", new=fast_jd):
        await Orchestrator(db, job_id).execute()
    return job_id


def _load_state(db, job_id: str) -> SharedState:
    db.expire_all()
    job = db.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    return SharedState(**job.workflow_state)


@pytest.mark.asyncio
async def test_gate_matrix_jd_review_approve_and_reject(db, monkeypatch):
    job_id = await _seed_job_at_jd_review(db, monkeypatch)

    st = _load_state(db, job_id)
    assert st.current_stage == PipelineStage.JD_REVIEW.value
    assert st.jd_approval == ApprovalStatus.PENDING.value

    # Reject at JD gate => back to JD_DRAFTING
    await resume_workflow(db, 1, job_id, "reject", {"human_feedback": "Revise JD."})
    db.commit()
    st = _load_state(db, job_id)
    assert st.jd_approval == ApprovalStatus.REJECTED.value
    assert st.current_stage == PipelineStage.JD_DRAFTING.value

    # Force back to JD_REVIEW for approve path check
    await resume_workflow(
        db,
        1,
        job_id,
        "approve",
        {
            "current_stage": PipelineStage.JD_REVIEW.value,
            "jd_approval": ApprovalStatus.PENDING.value,
            "human_feedback": "Looks good now.",
        },
    )
    db.commit()
    st = _load_state(db, job_id)
    assert st.jd_approval == ApprovalStatus.APPROVED.value
    assert st.current_stage == PipelineStage.SOURCING.value


@pytest.mark.asyncio
async def test_gate_matrix_shortlist_review_approve_and_reject(db, monkeypatch):
    job_id = await _seed_job_at_jd_review(db, monkeypatch)

    # Move workflow to shortlist_review (pending)
    await resume_workflow(db, 1, job_id, "approve", {"human_feedback": "Approve JD"})
    db.commit()
    await Orchestrator(db, job_id).execute()
    st = _load_state(db, job_id)
    assert st.current_stage == PipelineStage.SHORTLIST_REVIEW.value
    assert st.shortlist_approval == ApprovalStatus.PENDING.value

    # Reject shortlist => back to sourcing
    await resume_workflow(db, 1, job_id, "reject", {"human_feedback": "Need more candidates."})
    db.commit()
    st = _load_state(db, job_id)
    assert st.shortlist_approval == ApprovalStatus.REJECTED.value
    assert st.current_stage == PipelineStage.SOURCING.value

    # Reset to shortlist gate and approve => outreach
    await resume_workflow(
        db,
        1,
        job_id,
        "approve",
        {
            "current_stage": PipelineStage.SHORTLIST_REVIEW.value,
            "shortlist_approval": ApprovalStatus.PENDING.value,
            "human_feedback": "Proceed shortlist.",
        },
    )
    db.commit()
    st = _load_state(db, job_id)
    assert st.shortlist_approval == ApprovalStatus.APPROVED.value
    assert st.current_stage == PipelineStage.OUTREACH.value


@pytest.mark.asyncio
async def test_gate_matrix_hire_review_approve_and_reject(db, monkeypatch):
    job_id = await _seed_job_at_jd_review(db, monkeypatch)

    # Advance to hire_review (pending)
    await resume_workflow(db, 1, job_id, "approve", {"human_feedback": "Approve JD"})
    db.commit()
    await Orchestrator(db, job_id).execute()
    await resume_workflow(db, 1, job_id, "approve", {"human_feedback": "Approve shortlist"})
    db.commit()
    await Orchestrator(db, job_id).execute()

    st = _load_state(db, job_id)
    assert st.current_stage == PipelineStage.HIRE_REVIEW.value
    assert st.hire_approval == ApprovalStatus.PENDING.value

    # Reject final hire => back to decision
    await resume_workflow(db, 1, job_id, "reject", {"human_feedback": "Re-evaluate decision."})
    db.commit()
    st = _load_state(db, job_id)
    assert st.hire_approval == ApprovalStatus.REJECTED.value
    assert st.current_stage == PipelineStage.DECISION.value

    # Reset to hire gate and approve => offer
    await resume_workflow(
        db,
        1,
        job_id,
        "approve",
        {
            "current_stage": PipelineStage.HIRE_REVIEW.value,
            "hire_approval": ApprovalStatus.PENDING.value,
            "human_feedback": "Final approve.",
        },
    )
    db.commit()
    st = _load_state(db, job_id)
    assert st.hire_approval == ApprovalStatus.APPROVED.value
    assert st.current_stage == PipelineStage.OFFER.value
