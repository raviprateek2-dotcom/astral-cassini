"""Agent 5: Outreach Agent — Crafts personalized recruitment emails.

Generates tailored outreach messages for shortlisted candidates using
the job description and their specific resume/gap analysis.
"""

from __future__ import annotations

import logging
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import PipelineStage, SharedState, OutreachEmail

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

    async def outreach_node(state: SharedState) -> SharedState:
        """Generate personalized emails for shortlisted candidates."""
        if state.current_stage != PipelineStage.OUTREACH.value:
            return state

        job_title = state.job_title
        job_description = state.job_description
        candidates = state.scored_candidates

        outreach_emails: list[OutreachEmail] = []

        # Only process top 3 candidates for efficiency in this demo
        for candidate in candidates[:3]:
            user_prompt = f"""Draft a recruitment email for:
Candidate Name: {candidate.candidate_name}
Job Title: {job_title}
Key Strengths: {', '.join(candidate.strengths)}
Identified Gaps to address later: {', '.join(candidate.gaps)}

Context (JD):
{job_description[:1000]}
"""

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            try:
                if not settings.openai_api_key:
                    outreach_emails.append(
                        OutreachEmail(
                            candidate_id=candidate.candidate_id,
                            candidate_name=candidate.candidate_name,
                            subject=f"Opportunity at PRO HR: {job_title}",
                            body=f"Hi {candidate.candidate_name}, we would love to connect about the {job_title} role.",
                            status="sent",
                        )
                    )
                    continue
                llm = ChatOpenAI(
                    model=settings.llm_model,
                    temperature=0.7,
                    api_key=SecretStr(settings.openai_api_key),
                )
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

                outreach_emails.append(
                    OutreachEmail(
                        candidate_id=candidate.candidate_id,
                        candidate_name=candidate.candidate_name,
                        subject=str(email_data.get("subject", "")),
                        body=str(email_data.get("body", "")),
                        status="sent",
                    )
                )
                state.log_audit(
                    "Outreach Agent",
                    "outreach_sent",
                    f"Personalized email sent to {candidate.candidate_name}.",
                    PipelineStage.OUTREACH.value,
                )

            except Exception as e:
                logger.error(f"Outreach failed for {candidate.candidate_name}: {e}")
                continue

        state.outreach_emails = outreach_emails
        state.current_stage = PipelineStage.ENGAGEMENT.value
        return state

    return outreach_node
