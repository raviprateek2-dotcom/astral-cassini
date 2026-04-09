"""End-to-end: one job through every orchestrator stage until ``completed``.

Uses the real agent graph with ``openai_api_key`` cleared so JD / outreach / response / offer
use deterministic mocks. ``jd_architect_node`` is patched only to skip the 2s mock streaming delay.

Execution model matches production: ``Orchestrator.execute()`` until a HITL breakpoint, then
``resume_workflow(..., "approve", ...)``, repeat until ``PipelineStage.COMPLETED``.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.e2e

from app.config import settings
from app.core.orchestrator import Orchestrator, resume_workflow, start_workflow
from app.models.db_models import Job
from app.models.state import (
    ApprovalStatus,
    PipelineStage,
    SharedState,
)

VALID_JD = """## Role Summary
Own end-to-end QA outcomes for hiring workflow quality.

## Core Responsibilities
- Validate deterministic pipeline execution.

## Required Qualifications
- Python
- Testing

## Preferred Qualifications
- CI/CD

## Compensation & Benefits
- Competitive salary and benefits.

## Interview Process
- HR screen
- Technical round

## Equal Opportunity Statement
We are an equal opportunity employer.
"""


@pytest.mark.asyncio
async def test_full_recruitment_pipeline_every_stage_to_completed(db, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")

    async def fast_jd(state: SharedState) -> SharedState:
        jd = f"# {state.job_title}\n\nMock JD for full pipeline test.\n- Fast"
        return SharedState(
            **{
                **state.model_dump(),
                "job_description": jd,
                "current_stage": PipelineStage.JD_REVIEW.value,
                "jd_approval": ApprovalStatus.PENDING.value,
            }
        )

    def load_state() -> SharedState:
        db.expire_all()
        job = db.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None
        return SharedState(**job.workflow_state)

    async def run_until_halt() -> None:
        orchestrator = Orchestrator(db, job_id)
        await orchestrator.execute()

    result = await start_workflow(
        db,
        1,
        "Pipeline E2E All Stages",
        "QA",
        ["Python", "Testing"],
        preferred_qualifications=[],
    )
    job_id = result["job_id"]
    db.commit()

    # 1) JD drafting → JD review (HITL)
    with patch("app.core.orchestrator.jd_architect_node", new=fast_jd):
        await run_until_halt()
    st = load_state()
    assert st.current_stage == PipelineStage.JD_REVIEW.value
    assert st.jd_approval == ApprovalStatus.PENDING.value

    # 2) Approve JD → sourcing → screening → shortlist review (HITL)
    await resume_workflow(
        db,
        1,
        job_id,
        "approve",
        {"human_feedback": "Approved for sourcing.", "job_description": VALID_JD},
    )
    db.commit()
    await run_until_halt()
    st = load_state()
    assert st.current_stage == PipelineStage.SHORTLIST_REVIEW.value
    assert st.shortlist_approval == ApprovalStatus.PENDING.value
    assert len(st.scored_candidates) >= 1

    # 3) Approve shortlist → outreach → engagement → scheduling → interviewing → decision → hire review (HITL)
    await resume_workflow(
        db, 1, job_id, "approve", {"human_feedback": "Proceed to interviews."}
    )
    db.commit()
    await run_until_halt()
    st = load_state()
    assert st.current_stage == PipelineStage.HIRE_REVIEW.value
    assert st.hire_approval == ApprovalStatus.PENDING.value
    assert len(st.final_recommendations) >= 1

    # 4) Final hire approval → offer → completed
    await resume_workflow(db, 1, job_id, "approve", {"human_feedback": "Approved hire; draft offer."})
    db.commit()
    await run_until_halt()
    st = load_state()
    assert st.current_stage == PipelineStage.COMPLETED.value
    assert st.offer_details, "Expected at least one offer record at completion"
    assert st.hire_approval == ApprovalStatus.APPROVED.value
