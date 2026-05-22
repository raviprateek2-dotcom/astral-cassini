"""Agent 6: Response Tracker — Candidate replies and engagement evaluation.

In a production system, this would listen to webhooks from email or SMS providers.
For this version, it simulates responses to ensure the end-to-end pipeline is functional.
"""

from __future__ import annotations

import logging
import random
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import PipelineStage, SharedState, CandidateResponse
from app.agents.structured_outputs import ResponseIntentResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Candidate Lifecycle Specialist. 
Your role is to simulate a realistic response from a candidate who has received a personalized outreach email.

GUIDELINES:
1. Respond as the candidate, showing interest in the role.
2. Ask one or two clarifying questions (e.g., "What is the expected salary range?" or "Is the role fully remote?").
3. Make it realistic and professional.
4. Keep the response to 2-3 sentences.
"""

INTENT_CLASSIFIER_PROMPT = """Classify the candidate's response into one of these intents:
- "interested": Candidate expresses interest in the role or agrees to next steps.
- "declined": Candidate declines or withdraws from consideration.
- "questions_asked": Candidate asks clarifying questions about the role, company, or process.
- "reschedule_request": Candidate requests to reschedule or suggests alternative timing.

Also extract any specific questions the candidate asked.
Determine engagement level: High (interested), Medium (questions/reschedule), Low (declined)."""


def create_response_tracker():
    """Create the Response Tracker agent node function."""

    async def response_tracker_node(state: SharedState) -> SharedState:
        """Simulate candidate engagement. If no response, transitions to SCHEDULING."""
        if state.current_stage != PipelineStage.ENGAGEMENT.value:
            return state

        outreach_emails = state.outreach_emails
        if not outreach_emails:
            state.current_stage = PipelineStage.SCHEDULING.value
            return state
        if state.candidate_responses:
            state.log_audit(
                "Response Tracker",
                "response_ingested",
                f"Using {len(state.candidate_responses)} externally captured candidate responses.",
                PipelineStage.ENGAGEMENT.value,
            )
            state.current_stage = PipelineStage.SCHEDULING.value
            return state

        candidate_responses: list[CandidateResponse] = []

        # Process responses for candidates we reached out to
        for email in outreach_emails:
            candidate_id = email.candidate_id
            candidate_name = email.candidate_name

            user_prompt = f"""Generate a candidate response for:
Candidate: {candidate_name}
To email: {email.subject}
"""

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            try:
                if not settings.openai_api_key:
                    roll = random.random()
                    if roll < 0.70:
                        mock_intent, mock_engagement = "interested", "High"
                        mock_response = "Thanks for reaching out. I am interested and open to scheduling."
                    elif roll < 0.85:
                        mock_intent, mock_engagement = "questions_asked", "Medium"
                        mock_response = "Interesting role! Could you share more about the team structure and remote work policy?"
                    elif roll < 0.95:
                        mock_intent, mock_engagement = "reschedule_request", "Medium"
                        mock_response = "I am interested but currently traveling. Could we schedule for next week instead?"
                    else:
                        mock_intent, mock_engagement = "declined", "Low"
                        mock_response = "Thank you for the opportunity, but I have accepted another offer."
                    candidate_responses.append(
                        CandidateResponse(
                            candidate_id=str(candidate_id),
                            candidate_name=str(candidate_name),
                            response=mock_response,
                            engagement_level=mock_engagement,
                            intent=mock_intent,
                        )
                    )
                    continue
                llm = ChatOpenAI(
                    model=settings.llm_model,
                    temperature=0.7,
                    api_key=SecretStr(settings.openai_api_key),
                )
                response = await llm.ainvoke(messages)
                response_text = str(response.content)

                # Intent classification via structured output
                intent_llm = ChatOpenAI(
                    model=settings.llm_model,
                    temperature=0.0,
                    api_key=SecretStr(settings.openai_api_key),
                )
                intent_chain = intent_llm.with_structured_output(ResponseIntentResult)
                classification = await intent_chain.ainvoke([
                    SystemMessage(content=INTENT_CLASSIFIER_PROMPT),
                    HumanMessage(content=f"Candidate response:\n{response_text}"),
                ])

                candidate_responses.append(
                    CandidateResponse(
                        candidate_id=str(candidate_id),
                        candidate_name=str(candidate_name),
                        response=response_text,
                        engagement_level=classification.engagement_level,
                        intent=classification.intent,
                        extracted_questions=classification.extracted_questions,
                    )
                )
                state.log_audit(
                    "Response Tracker",
                    "response_received",
                    f"Candidate {candidate_name} expressed interest. Moving to Scheduling.",
                    PipelineStage.ENGAGEMENT.value,
                )

            except Exception as e:
                logger.error(f"Response tracking failed for {candidate_name}: {e}")
                continue

        state.candidate_responses = candidate_responses
        state.current_stage = PipelineStage.SCHEDULING.value
        return state

    return response_tracker_node
