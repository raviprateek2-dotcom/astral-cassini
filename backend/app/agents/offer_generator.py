"""Offer Generator — Generates final recruitment offer letters (offer pipeline stage).

Takes the recommendation from the Hiring Ops Coordinator / decider output and the job description to
draft a complete, professional offer letter from a template.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel, SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import PipelineStage, SharedState, OfferRecord

logger = logging.getLogger(__name__)

# --- Load offer template at module level ---
OFFER_TEMPLATE = (Path(__file__).parent / "offer_template.md").read_text(encoding="utf-8")

# --- Required legal sections that the rendered offer must contain ---
_REQUIRED_LEGAL_SECTIONS = ["Background Verification", "Equal Opportunity", "At-Will Employment"]

SYSTEM_PROMPT = """You are a Compensation and Benefits Specialist.
Generate ONLY the following fields as a JSON object:
- "benefits_summary": A brief list of key benefits (Medical, Equity, Vacation, etc.)
- "start_date": A reasonable start date (typically 2-4 weeks from now)
- "personalized_impact_statement": 2-3 sentences about the specific impact this candidate will have in the department.
"""


class OfferDynamicFields(BaseModel):
    benefits_summary: str
    start_date: str
    personalized_impact_statement: str


def _render_template(
    template: str,
    candidate_name: str,
    job_title: str,
    department: str,
    salary: str,
    benefits_summary: str,
    start_date: str,
    personalized_impact_statement: str,
) -> str:
    """Fill in the offer template placeholders."""
    rendered = template
    rendered = rendered.replace("{{candidate_name}}", candidate_name)
    rendered = rendered.replace("{{job_title}}", job_title)
    rendered = rendered.replace("{{department}}", department)
    rendered = rendered.replace("{{salary}}", salary)
    rendered = rendered.replace("{{benefits_summary}}", benefits_summary)
    rendered = rendered.replace("{{start_date}}", start_date)
    rendered = rendered.replace("{{personalized_impact_statement}}", personalized_impact_statement)
    return rendered


def _validate_legal_sections(rendered_offer: str) -> list[str]:
    """Check that the rendered offer contains required legal sections. Returns missing ones."""
    missing = [section for section in _REQUIRED_LEGAL_SECTIONS if section not in rendered_offer]
    return missing


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
            if rec.decision in ("hire", "strong_hire"):
                top_hire = rec
                break
        
        if not top_hire:
            # If no 'hire' but we are in the OFFER stage, take the highest score 'maybe' or the first one
            top_hire = recommendations[0]

        job_title = state.job_title
        department = state.department
        salary_range = state.salary_range or "Competitive"

        if not settings.openai_api_key:
            # Mock path — use template with hardcoded placeholder values
            offer_markdown = _render_template(
                OFFER_TEMPLATE,
                candidate_name=top_hire.candidate_name,
                job_title=job_title,
                department=department,
                salary=salary_range,
                benefits_summary="Medical, Dental, Vision, 401(k) match, Equity, 20 days PTO",
                start_date="TBD (2-4 weeks from acceptance)",
                personalized_impact_statement="We believe you will make a significant contribution to our team and look forward to the impact you will bring.",
            )
            missing = _validate_legal_sections(offer_markdown)
            if missing:
                logger.warning(f"Mock offer letter missing required legal sections: {missing}")
            state.offer_details = [
                OfferRecord(
                    candidate_id=top_hire.candidate_id,
                    candidate_name=top_hire.candidate_name,
                    offer_markdown=offer_markdown,
                    salary_offered=salary_range,
                    benefits_summary="Standard company benefits package.",
                    status="draft",
                    valid_until="5 business days",
                )
            ]
            state.current_stage = PipelineStage.COMPLETED.value
            return state

        user_prompt = f"""Generate the dynamic fields for an offer letter:
Candidate Name: {top_hire.candidate_name}
Job Title: {job_title}
Department: {department}
Offered Salary: {salary_range}
Reasoning: {top_hire.reasoning}
"""

        try:
            llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=0.3,
                api_key=SecretStr(settings.openai_api_key),
            )
            structured_llm = llm.with_structured_output(OfferDynamicFields)
            dynamic_fields: OfferDynamicFields = await structured_llm.ainvoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])

            offer_markdown = _render_template(
                OFFER_TEMPLATE,
                candidate_name=top_hire.candidate_name,
                job_title=job_title,
                department=department,
                salary=salary_range,
                benefits_summary=dynamic_fields.benefits_summary,
                start_date=dynamic_fields.start_date,
                personalized_impact_statement=dynamic_fields.personalized_impact_statement,
            )

            missing = _validate_legal_sections(offer_markdown)
            if missing:
                logger.warning(f"Rendered offer letter missing required legal sections: {missing}")

            state.offer_details = [
                OfferRecord(
                    candidate_id=top_hire.candidate_id,
                    candidate_name=top_hire.candidate_name,
                    offer_markdown=offer_markdown,
                    salary_offered=salary_range,
                    benefits_summary=dynamic_fields.benefits_summary,
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
            # Fallback — use template with hardcoded values
            fallback_markdown = _render_template(
                OFFER_TEMPLATE,
                candidate_name=top_hire.candidate_name,
                job_title=job_title,
                department=department,
                salary=salary_range,
                benefits_summary="Standard benefits package",
                start_date="TBD",
                personalized_impact_statement="We look forward to your contributions.",
            )
            state.offer_details = [
                OfferRecord(
                    candidate_id=top_hire.candidate_id,
                    candidate_name=top_hire.candidate_name,
                    offer_markdown=fallback_markdown,
                    status="error",
                )
            ]
            state.current_stage = PipelineStage.COMPLETED.value
            return state

    return offer_generator_node
