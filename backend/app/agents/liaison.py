"""Agent 2: The Liaison — Human-in-the-loop approval gatekeeper.

Manages three critical approval checkpoints in the pipeline by logging
notices to the exact state and letting the orchestrator hit the breakpoint.
"""

from __future__ import annotations

import json
from datetime import datetime

from app.models.state import SharedState, PipelineStage


async def liaison_node(state: SharedState) -> SharedState:
    """Check the current stage and set up the HITL gate.
    Returns the state unmodified beyond adding Audit elements.
    """

    current_stage = state.current_stage

    if current_stage == PipelineStage.JD_REVIEW.value:
        state.log_audit(
            agent="The Liaison",
            action="ghosting_prevention_update",
            details="Liaison Update: Notifying relevant parties that the Job Description is ready for review.",
            stage=PipelineStage.JD_REVIEW.value
        )
        state.log_audit(
            agent="The Liaison",
            action="awaiting_jd_approval",
            details="Job description is ready for human review",
            stage=PipelineStage.JD_REVIEW.value
        )
            
    elif current_stage == PipelineStage.SHORTLIST_REVIEW.value:
        scored = state.scored_candidates
        state.log_audit(
            agent="The Liaison",
            action="ghosting_prevention_update",
            details=f"Liaison Update: Sending a 'Soft Pulse' update to {len(scored)} candidates. Informing them that shortlisting is underway to prevent ghosting.",
            stage=PipelineStage.SHORTLIST_REVIEW.value
        )
        state.log_audit(
            agent="The Liaison",
            action="awaiting_shortlist_approval",
            details=f"Shortlist of {len(scored)} scored candidates ready for review",
            stage=PipelineStage.SHORTLIST_REVIEW.value
        )

    elif current_stage == PipelineStage.HIRE_REVIEW.value:
        recs = state.final_recommendations
        state.log_audit(
            agent="The Liaison",
            action="ghosting_prevention_update",
            details="Liaison Update: Proactively updating high-potential candidates that final deliberations are in progress. Maintaining high engagement.",
            stage=PipelineStage.HIRE_REVIEW.value
        )
        state.log_audit(
            agent="The Liaison",
            action="awaiting_hire_decision",
            details=f"Final recommendations for {len(recs)} candidates ready for review",
            stage=PipelineStage.HIRE_REVIEW.value
        )

    return state
