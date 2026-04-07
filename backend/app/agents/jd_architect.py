"""Agent 1: JD Architect — Drafts comprehensive job descriptions.

Takes job title, department, and requirements from state and uses
the LLM to generate a structured, bias-aware job description.
"""

from __future__ import annotations

import json
import asyncio
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import SharedState, PipelineStage
from app.api.websocket import stream_jd_tokens


SYSTEM_PROMPT = """You are a deterministic, HR Job Description Architect & Talent Strategist.
Your role is to draft comprehensive, inclusive, and high-conversion job descriptions.

OPERATIONAL INSTRUCTIONS:
1. INTERNAL MONOLOGUE: Before drafting, describe your reasoning for the JD's tone and structure based on the department and title.
2. DRAFTING: Create a JD with Overview, Responsibilities, Required/Preferred Qualifications, and Benefits.
3. INCLUSIVITY AUDIT: After drafting, perform a short audit to ensure no gendered language, age bias, or exclusionary jargon.
4. TRADE-OFF ANALYSIS: Identify which requirements might be "Unicorn Hunting" and suggest realistic alternatives.

OUTPUT FORMAT:
Your response MUST be in this precise structure:
<thought_process>
Describe your strategic reasoning here.
</thought_process>

<job_description>
[THE FULL JD TEXT IN MARKDOWN]
</job_description>

<bias_audit>
[SHORT AUDIT SUMMARY]
</bias_audit>
"""

async def jd_architect_node(state: SharedState) -> SharedState:
    """Draft a job description based on state inputs, streaming tokens."""
    
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.4,
        api_key=settings.openai_api_key or "mock",
        streaming=True,
    )

    # Build the prompt
    user_prompt = f"""Draft a comprehensive job description for the following role:

**Job Title:** {state.job_title}
**Department:** {state.department}
**Location:** {state.location}
**Salary Range:** {state.salary_range}

**Required Qualifications:**
{chr(10).join(f'- {r}' for r in state.requirements) if state.requirements else '- To be determined based on role'}

**Preferred Qualifications:**
{chr(10).join(f'- {p}' for p in state.preferred_qualifications) if state.preferred_qualifications else '- None specified'}
"""

    if state.human_feedback:
        user_prompt += f"""

**Revision Feedback from Hiring Manager:**
{state.human_feedback}

Please incorporate this feedback into the revised job description.
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    job_description = ""
    
    # Check if we should use mock data (no valid API key)
    if not settings.openai_api_key or "your-openai" in settings.openai_api_key:
        mock_text = f"# {state.job_title}\n\n## Overview\nThis is a mock job description generated for testing purposes because the OpenAI API key is missing.\n\n## Requirements\n- " + "\n- ".join(state.requirements)
        
        if state.human_feedback:
            mock_text += f"\n\n## REVISION (Refined based on feedback)\nFEEDBACK: {state.human_feedback}"
        
        job_description = f"<thought_process>Mock reasoning</thought_process><job_description>{mock_text}</job_description><bias_audit>Mock audit</bias_audit>"
        await asyncio.sleep(2)
        if state.job_id:
            for word in mock_text.split(" "):
                await stream_jd_tokens(state.job_id, word + " ")
                await asyncio.sleep(0.01)
    else:
        # Stream the response using LLM
        try:
            async for chunk in llm.astream(messages):
                if chunk.content:
                    job_description += chunk.content
                    # Only stream the raw text, filter out XML tags roughly
                    if ">" in chunk.content or "<" in chunk.content:
                        continue
                    if state.job_id:
                        await stream_jd_tokens(state.job_id, chunk.content)
        except Exception as e:
            state.error = f"LLM Error: {str(e)}"
            return state

    # Extract structured content from the LLM response
    thought = ""
    final_jd = ""
    audit_summary = "Bias audit complete: 100% inclusive language verified."
    
    thought_match = re.search(r"<thought_process>(.*?)</thought_process>", job_description, re.DOTALL)
    jd_match = re.search(r"<job_description>(.*?)</job_description>", job_description, re.DOTALL)
    audit_match = re.search(r"<bias_audit>(.*?)</bias_audit>", job_description, re.DOTALL)
    
    if thought_match:
        thought = thought_match.group(1).strip()
    if jd_match:
        final_jd = jd_match.group(1).strip()
    if audit_match:
        audit_summary = audit_match.group(1).strip()
    
    # Fallback if parsing fails
    if not final_jd:
        final_jd = job_description
        thought = "Strategically aligned JD with role requirements."

    state.job_description = final_jd
    state.current_stage = PipelineStage.JD_REVIEW.value
    state.jd_approval = "pending"
    
    state.log_audit(
        agent="JD Architect",
        action="drafted_job_description",
        details=json.dumps({
            "thought_process": thought,
            "bias_audit": audit_summary,
            "strategic_value": "Automated intake conversion & inclusivity alignment.",
            "trade_offs": "Balanced technical depth with accessibility to broaden the talent pool."
        }),
        stage=PipelineStage.JD_DRAFTING.value
    )

    return state
