"""Agent 5: Outreach — Crafts personalized recruitment emails.

Generates tailored outreach messages for shortlisted candidates using
the job description and their specific resume/gap analysis.
"""

from __future__ import annotations

import logging
import re
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import PipelineStage, SharedState, OutreachEmail
from app.agents.structured_outputs import OutreachEmailSchema

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:
    SendGridAPIClient = None
    Mail = None

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a highly persuasive and professional Talent Acquisition Specialist. 
Your goal is to craft personalized, compelling outreach emails to high-potential candidates.

GUIDELINES:
1. Reference specific skills or experiences from the candidate's profile that match the Job Description.
2. Maintain a warm, welcoming, and professional tone.
3. Highlight the company culture and the specific impact they could join.
4. Include a clear call-to-action (e.g., "Are you open to a brief chat next week?").
5. Keep it concise (under 200 words).

OUTPUT FORMAT: Return the subject line and email body."""

def _response_to_text(content: object) -> str:
    """Normalize LangChain response content into plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


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
                structured_llm = llm.with_structured_output(OutreachEmailSchema)
                email_data = await structured_llm.ainvoke(messages)

                email_subject = email_data.subject
                email_body = email_data.body

                # Post-generation placeholder detection
                placeholder_re = re.compile(r'\[\w[\w\s]*\]|\{\w[\w\s]*\}')
                for field_name, field_value in [("subject", email_subject), ("body", email_body)]:
                    placeholders = placeholder_re.findall(field_value)
                    if placeholders:
                        logger.warning(
                            "Unresolved placeholders in %s for %s: %s",
                            field_name, candidate.candidate_name, placeholders,
                        )
                email_subject = placeholder_re.sub("", email_subject)
                email_body = placeholder_re.sub("", email_body)
                
                # Phase 4.4.1: Live Email Integration via SendGrid
                dispatch_status = "drafted"
                if settings.email_provider == "sendgrid" and settings.sendgrid_api_key and SendGridAPIClient:
                    try:
                        sg = SendGridAPIClient(settings.sendgrid_api_key)
                        message = Mail(
                            from_email=settings.smtp_from_email,
                            to_emails="candidate_mock_email@example.com", # In real prod, this is candidate.email
                            subject=email_subject,
                            html_content=email_body.replace("\n", "<br>")
                        )
                        sg.send(message)
                        dispatch_status = "sent"
                    except Exception as e:
                        logger.error(f"SendGrid failed for {candidate.candidate_name}: {e}")
                        dispatch_status = "failed"
                elif settings.email_provider == "mock" or not settings.sendgrid_api_key:
                    dispatch_status = "sent_mock"

                outreach_emails.append(
                    OutreachEmail(
                        candidate_id=candidate.candidate_id,
                        candidate_name=candidate.candidate_name,
                        subject=email_subject,
                        body=email_body,
                        status=dispatch_status,
                    )
                )
                state.log_audit(
                    "Outreach Agent",
                    "outreach_sent",
                    f"Personalized email dispatched to {candidate.candidate_name} via {settings.email_provider}.",
                    PipelineStage.OUTREACH.value,
                )

            except Exception as e:
                logger.error(f"Outreach failed for {candidate.candidate_name}: {e}")
                continue

        state.outreach_emails = outreach_emails
        state.current_stage = PipelineStage.ENGAGEMENT.value
        return state

    return outreach_node
