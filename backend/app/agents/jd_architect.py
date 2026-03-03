"""Agent 1: JD Architect — Drafts comprehensive job descriptions.

Takes job title, department, and requirements from state and uses
the LLM to generate a structured, bias-aware job description.
"""

from __future__ import annotations

import json
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import RecruitmentState, PipelineStage
from app.api.websocket import stream_jd_tokens


SYSTEM_PROMPT = """You are a world-class HR Job Description Architect. Your role is to
draft comprehensive, inclusive, and compelling job descriptions.

GUIDELINES:
1. Structure the JD clearly with sections: Overview, Responsibilities, Required
   Qualifications, Preferred Qualifications, Benefits & Perks, and Equal Opportunity
   Statement.
2. Use inclusive, gender-neutral language throughout.
3. Avoid unnecessary jargon or overly strict requirements that could exclude
   qualified diverse candidates.
4. Focus on outcomes and competencies rather than years of experience where possible.
5. Include a salary range if provided.
6. Make the role sound exciting and the company culture welcoming.

OUTPUT FORMAT: Return ONLY the job description text, well-formatted with markdown headers."""


def create_jd_architect():
    """Create the JD Architect agent node function."""

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.4,
        api_key=settings.openai_api_key,
        streaming=True,
    )

    async def jd_architect_node(state: RecruitmentState) -> dict:
        """Draft a job description based on state inputs, streaming tokens."""

        job_id = state.get("job_id", "")
        job_title = state.get("job_title", "Software Engineer")
        department = state.get("department", "Engineering")
        requirements = state.get("requirements", [])
        preferred = state.get("preferred_qualifications", [])
        location = state.get("location", "Remote")
        salary_range = state.get("salary_range", "Competitive")
        human_feedback = state.get("human_feedback", "")

        # DEBUG: Add entry to see if node starts
        start_audit = {
            "timestamp": datetime.now().isoformat(),
            "agent": "JD Architect",
            "action": "node_entered",
            "details": "Entered jd_architect_node, starting LLM stream...",
            "stage": PipelineStage.JD_DRAFTING.value,
        }
        # We can't return yet, but we can't easily sync to DB from here without a session.
        # So we just proceed and hope it finishes.
        # Actually, let's try to print to stdout too.
        print(f"DEBUG: Entering jd_architect_node for job {job_id}")

        # Build the prompt
        user_prompt = f"""Draft a comprehensive job description for the following role:

**Job Title:** {job_title}
**Department:** {department}
**Location:** {location}
**Salary Range:** {salary_range}

**Required Qualifications:**
{chr(10).join(f'- {r}' for r in requirements) if requirements else '- To be determined based on role'}

**Preferred Qualifications:**
{chr(10).join(f'- {p}' for p in preferred) if preferred else '- None specified'}
"""

        if human_feedback:
            user_prompt += f"""

**Revision Feedback from Hiring Manager:**
{human_feedback}

Please incorporate this feedback into the revised job description.
"""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        job_description = ""
        # Stream the response
        async for chunk in llm.astream(messages):
            if chunk.content:
                job_description += chunk.content
                if job_id:
                    await stream_jd_tokens(job_id, chunk.content)

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "JD Architect",
            "action": "drafted_job_description",
            "details": f"Generated JD for {job_title} in {department}",
            "stage": PipelineStage.JD_DRAFTING.value,
        }

        return {
            "job_description": job_description,
            "current_stage": PipelineStage.JD_REVIEW.value,
            "jd_approval": "pending",
            "audit_log": [audit_entry],
        }

    return jd_architect_node
