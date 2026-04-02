"""Agent 10: Offer Generator — Generates final recruitment offer letters.

Takes the recommendation from The Decider and the job description to
draft a complete, professional offer letter in Markdown.
"""

from __future__ import annotations

import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import RecruitmentState, PipelineStage

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

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.3,
        api_key=settings.openai_api_key,
    )

    async def offer_generator_node(state: RecruitmentState) -> dict:
        """Generate an offer letter for the top recommended candidate."""
        
        current_stage = state.get("current_stage")
        if current_stage != PipelineStage.OFFER.value:
            return {}

        recommendations = state.get("final_recommendations", [])
        if not recommendations:
            return {"current_stage": PipelineStage.COMPLETED.value}

        # Select the top 'hire' recommendation
        top_hire = None
        for rec in recommendations:
            if rec.get("decision") == "hire":
                top_hire = rec
                break
        
        if not top_hire:
            # If no 'hire' but we are in the OFFER stage, take the highest score 'maybe' or the first one
            top_hire = recommendations[0]

        job_title = state.get("job_title", "")
        department = state.get("department", "")
        salary_range = state.get("salary_range", "Competitive")

        user_prompt = f"""Generate an offer letter for:
Candidate Name: {top_hire.get('candidate_name')}
Job Title: {job_title}
Department: {department}
Offered Salary: {salary_range}
Reasoning: {top_hire.get('reasoning')}
"""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await llm.ainvoke(messages)
            
            offer_record = {
                "candidate_id": top_hire.get("candidate_id"),
                "candidate_name": top_hire.get("candidate_name"),
                "offer_markdown": response.content,
                "salary_offered": salary_range,
                "status": "draft",
                "valid_until": "5 business days"
            }

            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": "Offer Generator",
                "action": "offer_letter_drafted",
                "details": f"Professional offer letter drafted for {top_hire.get('candidate_name')}.",
                "stage": PipelineStage.OFFER.value,
            }

            return {
                "offer_details": [offer_record],
                "audit_log": [audit_entry],
                "current_stage": PipelineStage.COMPLETED.value
            }

        except Exception as e:
            logger.error(f"Offer generation failed: {e}")
            return {"current_stage": PipelineStage.COMPLETED.value}

    return offer_generator_node
