"""Agent 6: Response Tracker — Simulates candidate replies and evaluates engagement.

In a production system, this would listen to webhooks from email or SMS providers.
For this version, it simulates responses to ensure the end-to-end pipeline is functional.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import PipelineStage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Candidate Lifecycle Specialist. 
Your role is to simulate a realistic response from a candidate who has received a personalized outreach email.

GUIDELINES:
1. Respond as the candidate, showing interest in the role.
2. Ask one or two clarifying questions (e.g., "What is the expected salary range?" or "Is the role fully remote?").
3. Make it realistic and professional.
4. Keep the response to 2-3 sentences.
"""


def create_response_tracker():
    """Create the Response Tracker agent node function."""

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.7,
        api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
    )

    async def response_tracker_node(state: dict[str, Any]) -> dict:
        """Simulate candidate engagement. If no response, transitions to SCHEDULING."""
        
        current_stage = state.get("current_stage")
        if current_stage != PipelineStage.ENGAGEMENT.value:
            return {}

        outreach_emails = state.get("outreach_emails", [])
        if not outreach_emails:
            return {"current_stage": PipelineStage.SCHEDULING.value}

        candidate_responses = []
        audit_logs = []

        # Process responses for candidates we reached out to
        for email in outreach_emails:
            candidate_id = email.get("candidate_id")
            candidate_name = email.get("candidate_name")

            user_prompt = f"""Generate a candidate response for:
Candidate: {candidate_name}
To email: {email.get('subject')}
"""

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            try:
                response = await llm.ainvoke(messages)
                
                candidate_responses.append({
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "response": response.content,
                    "engagement_level": "High"
                })

                audit_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "agent": "Response Tracker",
                    "action": "response_received",
                    "details": f"Candidate {candidate_name} expressed interest. Moving to Scheduling.",
                    "stage": PipelineStage.ENGAGEMENT.value,
                })

            except Exception as e:
                logger.error(f"Response tracking failed for {candidate_name}: {e}")
                continue

        return {
            "candidate_responses": candidate_responses,
            "audit_log": [audit_logs[-1]] if audit_logs else [],
            "current_stage": PipelineStage.SCHEDULING.value
        }

    return response_tracker_node
