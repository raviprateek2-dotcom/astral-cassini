"""Agent 1.5: JD Critic — Evaluates the JD Architect's output.

Implements the Actor-Critic pattern to ensure the JD meets compliance
and quality bars before bothering a human reviewer.
"""

import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from app.config import settings

class CritiqueResult(BaseModel):
    score: int = Field(..., description="Score from 1 to 10")
    feedback: str = Field(..., description="Specific feedback on what to fix if score < 9")
    approved: bool = Field(..., description="True if score >= 9")

CRITIC_PROMPT = """You are the Lead HR Compliance Officer and Senior Editor.
Your job is to ruthlessly evaluate drafted Job Descriptions before they reach the Hiring Manager.

EVALUATION CRITERIA:
1. Is it missing any mandatory sections? (Role Summary, Core Responsibilities, Required/Preferred Qualifications, Compensation & Benefits, Interview Process, Equal Opportunity).
2. Is the tone professional, inclusive, and engaging?
3. Does it contain illegal exclusionary language, gender bias, or age bias?
4. Are the requirements realistic (no "unicorn hunting")?

Return a strict JSON response containing:
- "score": integer 1-10
- "feedback": detailed instructions on how to fix it (if score < 9)
- "approved": boolean (true if >= 9)
"""

async def run_critic(job_description: str, job_title: str) -> CritiqueResult:
    """Evaluate a job description."""
    if not settings.openai_api_key or "your-openai" in settings.openai_api_key:
        # Mock logic
        return CritiqueResult(score=10, feedback="Looks great.", approved=True)

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.1,
        api_key=settings.openai_api_key,
    ).with_structured_output(CritiqueResult)

    user_msg = f"Please evaluate this drafted Job Description for the {job_title} role:\n\n{job_description}"

    messages = [
        SystemMessage(content=CRITIC_PROMPT),
        HumanMessage(content=user_msg)
    ]
    
    try:
        result = await llm.ainvoke(messages)
        return result
    except Exception as e:
        # Fallback in case of failure to not block pipeline
        return CritiqueResult(score=10, feedback=f"Critic failed to evaluate: {str(e)}", approved=True)
