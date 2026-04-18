"""Orchestration scheduling: coalesced re-run when start fires during an active task."""

import asyncio
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration

from app.models.db_models import Job
from app.models.state import PipelineStage, SharedState


@pytest.mark.asyncio
async def test_concurrent_start_orchestration_coalesces_followup(db):
    """Two overlapping starts for the same job yield one follow-up run (pending bit), not duplicate races."""
    import app.core.orchestrator as orch

    p = getattr(orch, "_orch_start_patcher_for_tests", None)
    if p is None:
        pytest.skip("Orchestration mock patcher not configured")

    job_id = "coal-001"
    state = SharedState(
        job_id=job_id,
        job_title="Coalesce",
        department="QA",
        current_stage=PipelineStage.JD_REVIEW.value,
        jd_approval="pending",
    )
    db.add(
        Job(
            job_id=job_id,
            job_title="Coalesce",
            department="QA",
            workflow_state=state.model_dump(mode="json"),
            current_stage=PipelineStage.JD_REVIEW.value,
            created_by_id=1,
        )
    )
    db.commit()

    orch._running_jobs.discard(job_id)
    orch._pending_orch_rerun.discard(job_id)

    p.stop()
    try:
        runs: list[str] = []
        orig = orch._run_orchestration_task

        async def instrumented_run(jid: str) -> None:
            runs.append(jid)
            await orig(jid)

        with patch.object(orch, "_run_orchestration_task", side_effect=instrumented_run):
            await asyncio.gather(
                orch.start_orchestration(job_id),
                orch.start_orchestration(job_id),
            )
            await asyncio.sleep(0.05)
        assert runs.count(job_id) >= 2, f"expected coalesced follow-up, got runs={runs!r}"
    finally:
        orch._running_jobs.discard(job_id)
        orch._pending_orch_rerun.discard(job_id)
        p.start()
