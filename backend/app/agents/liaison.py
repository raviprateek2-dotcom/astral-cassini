"""Agent 2: The Liaison — Human-in-the-loop approval gatekeeper.

Manages three critical approval checkpoints in the pipeline:
1. JD Approval — after Agent 1 drafts the job description
2. Shortlist Approval — after Agent 4 scores candidates
3. Hire Decision Approval — after Agent 7 makes recommendations

This agent pauses the workflow and waits for human input via the API.
"""

from __future__ import annotations

from datetime import datetime

from app.models.state import RecruitmentState, PipelineStage


def create_liaison():
    """Create the Liaison (HITL gatekeeper) agent node function."""

    def liaison_node(state: RecruitmentState) -> dict:
        """Check the current stage and set up the HITL gate.

        The actual approval/rejection is handled by the API endpoint.
        This node prepares the state for human review.
        """

        current_stage = state.get("current_stage", "")
        audit_entries = []

        if current_stage == PipelineStage.JD_REVIEW.value:
            audit_entries.append({
                "timestamp": datetime.now().isoformat(),
                "agent": "The Liaison",
                "action": "awaiting_jd_approval",
                "details": "Job description is ready for human review",
                "stage": PipelineStage.JD_REVIEW.value,
            })
            return {
                "current_stage": PipelineStage.JD_REVIEW.value,
                "audit_log": audit_entries,
            }

        elif current_stage == PipelineStage.SHORTLIST_REVIEW.value:
            scored = state.get("scored_candidates", [])
            audit_entries.append({
                "timestamp": datetime.now().isoformat(),
                "agent": "The Liaison",
                "action": "awaiting_shortlist_approval",
                "details": f"Shortlist of {len(scored)} scored candidates ready for review",
                "stage": PipelineStage.SHORTLIST_REVIEW.value,
            })
            return {
                "current_stage": PipelineStage.SHORTLIST_REVIEW.value,
                "audit_log": audit_entries,
            }

        elif current_stage == PipelineStage.HIRE_REVIEW.value:
            recs = state.get("final_recommendations", [])
            audit_entries.append({
                "timestamp": datetime.now().isoformat(),
                "agent": "The Liaison",
                "action": "awaiting_hire_decision",
                "details": f"Final recommendations for {len(recs)} candidates ready for review",
                "stage": PipelineStage.HIRE_REVIEW.value,
            })
            return {
                "current_stage": PipelineStage.HIRE_REVIEW.value,
                "audit_log": audit_entries,
            }

        return {"audit_log": audit_entries}

    return liaison_node


def check_jd_approval(state: RecruitmentState) -> str:
    """Conditional edge: route based on JD approval status."""
    approval = state.get("jd_approval", "pending")
    if approval == "approved":
        return "approved"
    elif approval == "rejected":
        return "rejected"
    return "pending"


def check_shortlist_approval(state: RecruitmentState) -> str:
    """Conditional edge: route based on shortlist approval status."""
    approval = state.get("shortlist_approval", "pending")
    if approval == "approved":
        return "approved"
    elif approval == "rejected":
        return "rejected"
    return "pending"


def check_hire_approval(state: RecruitmentState) -> str:
    """Conditional edge: route based on hire decision approval status."""
    approval = state.get("hire_approval", "pending")
    if approval == "approved":
        return "approved"
    elif approval == "rejected":
        return "rejected"
    return "pending"
