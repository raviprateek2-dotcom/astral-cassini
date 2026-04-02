"""Agent 5: Outreach Agent — Crafts personalized recruitment emails.

Generates tailored outreach messages for shortlisted candidates using
the job description and their specific resume/gap analysis.
"""

from __future__ import annotations

import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import RecruitmentState, PipelineStage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a highly persuasive and professional Talent Acquisition Specialist. 
Your goal is to craft personalized, compelling outreach emails to high-potential candidates.

GUIDELINES:
1. Reference specific skills or experiences from the candidate's profile that match the Job Description.
2. Maintain a warm, welcoming, and professional tone.
3. Highlight the company culture and the specific impact they could join.
4. Include a clear call-to-action (e.g., "Are you open to a brief chat next week?").
5. Keep it concise (under 200 words).

OUTPUT FORMAT: Return a JSON object with "subject" and "body" keys."""


def create_outreach_agent():
    """Create the Outreach Agent node function."""

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.7,
        api_key=settings.openai_api_key,
    )

    async def outreach_node(state: RecruitmentState) -> dict:
        """Generate personalized emails for shortlisted candidates."""
        
        current_stage = state.get("current_stage")
        if current_stage != PipelineStage.OUTREACH.value:
            return {}

        job_title = state.get("job_title", "")
        job_description = state.get("job_description", "")
        # In a real flow, we only outreach to candidates who were 'approved' in the shortlist review.
        # For simplicity in this graph branch, we'll process the scored_candidates.
        candidates = state.get("scored_candidates", [])
        
        outreach_emails = []
        audit_logs = []

        # Only process top 3 candidates for efficiency in this demo
        for candidate in candidates[:3]:
            user_prompt = f"""Draft a recruitment email for:
Candidate Name: {candidate.get('candidate_name')}
Job Title: {job_title}
Key Strengths: {', '.join(candidate.get('strengths', []))}
Identified Gaps to address later: {', '.join(candidate.get('gaps', []))}

Context (JD):
{job_description[:1000]}
"""

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            try:
                # Use structured output if possible, but simple JSON parse for now
                response = await llm.ainvoke(messages)
                import json
                try:
                    # Attempt to extract JSON from markdown if necessary
                    content = response.content.strip()
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    email_data = json.loads(content)
                except Exception:
                    email_data = {
                        "subject": f"Opportunity at PRO HR: {job_title}",
                        "body": response.content
                    }

                outreach_emails.append({
                    "candidate_id": candidate.get("candidate_id"),
                    "candidate_name": candidate.get("candidate_name"),
                    "subject": email_data.get("subject"),
                    "body": email_data.get("body"),
                    "status": "sent"
                })

                audit_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "agent": "Outreach Agent",
                    "action": "outreach_sent",
                    "details": f"Personalized email sent to {candidate.get('candidate_name')}.",
                    "stage": PipelineStage.OUTREACH.value,
                })

            except Exception as e:
                logger.error(f"Outreach failed for {candidate.get('candidate_name')}: {e}")
                continue

        return {
            "outreach_emails": outreach_emails,
            "audit_log": audit_logs,
            "current_stage": PipelineStage.ENGAGEMENT.value
        }

    return outreach_node
