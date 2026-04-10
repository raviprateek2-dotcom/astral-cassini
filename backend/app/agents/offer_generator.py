"""Offer Generator — Generates final recruitment offer letters (offer pipeline stage).

Takes the recommendation from the Hiring Ops Coordinator / decider output and the job description to
draft a complete, professional offer letter in Markdown.
"""

from __future__ import annotations

import logging
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import PipelineStage, SharedState, OfferRecord

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Compensation and Benefits Specialist. 
Your goal is to generate a comprehensive, professional offer letter for a successful candidate.

GUIDELINES:
1. Include: Role Title, Salary, Key Benefits (Medical, Equity, Vacation), and Start Date.
2. Maintain a welcoming and celebratory tone.
3. Mention the specific impact the candidate will have in the department.
4. Clearly state the offer is subject to reference and background checks.
5. Provide a clear acceptance deadline (usually 5 business days).

OUTPUT FORMAT: Return only the Markdown formatted offer letter."""


def create_offer_generator():
    """Create the Offer Generator agent node function."""

    async def offer_generator_node(state: SharedState) -> SharedState:
        """Generate an offer letter for the top recommended candidate."""
        if state.current_stage != PipelineStage.OFFER.value:
            return state

        recommendations = state.final_recommendations
        if not recommendations:
            state.current_stage = PipelineStage.COMPLETED.value
            return state

        # Select the top 'hire' recommendation
        top_hire = None
        for rec in recommendations:
            if rec.decision == "hire":
                top_hire = rec
                break
        
        if not top_hire:
            # If no 'hire' but we are in the OFFER stage, take the highest score 'maybe' or the first one
            top_hire = recommendations[0]

        job_title = state.job_title
        department = state.department
        salary_range = state.salary_range or "Competitive"

        user_prompt = f"""Generate an offer letter for:
Candidate Name: {top_hire.candidate_name}
Job Title: {job_title}
Department: {department}
Offered Salary: {salary_range}
Reasoning: {top_hire.reasoning}
"""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            if not settings.openai_api_key:
                state.offer_details = [
                    OfferRecord(
                        candidate_id=top_hire.candidate_id,
                        candidate_name=top_hire.candidate_name,
                        offer_markdown="# Offer Letter\n\nMock offer generated without LLM key.",
                        salary_offered=salary_range,
                        benefits_summary="Standard company benefits package.",
                        status="draft",
                        valid_until="5 business days",
                    )
                ]
                state.current_stage = PipelineStage.COMPLETED.value
                return state
            llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=0.3,
                api_key=SecretStr(settings.openai_api_key),
            )
            response = await llm.ainvoke(messages)
            
            state.offer_details = [
                OfferRecord(
                    candidate_id=top_hire.candidate_id,
                    candidate_name=top_hire.candidate_name,
                    offer_markdown=str(response.content),
                    salary_offered=salary_range,
                    benefits_summary="Standard company benefits package.",
                    status="draft",
                    valid_until="5 business days",
                )
            ]
            state.log_audit(
                "Offer Generator",
                "offer_letter_drafted",
                f"Professional offer letter drafted for {top_hire.candidate_name}.",
                PipelineStage.COMPLETED.value,
            )
            state.current_stage = PipelineStage.COMPLETED.value
            return state

        except Exception as e:
            logger.error(f"Offer generation failed: {e}")
            state.offer_details = [
                OfferRecord(
                    candidate_id=top_hire.candidate_id,
                    candidate_name=top_hire.candidate_name,
                    offer_markdown="# Offer\n\nAutomatic generation failed; see logs.",
                    status="error",
                )
            ]
            state.current_stage = PipelineStage.COMPLETED.value
            return state

    return offer_generator_node
