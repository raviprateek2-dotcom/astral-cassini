"""Agent 4: The Screener — Gap analysis and candidate scoring.

Evaluates each candidate against the job requirements, producing
a score from 0-100 with explainable reasoning across multiple
dimensions: skills match, experience, education, and cultural fit.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import RecruitmentState, PipelineStage

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an expert HR Screening Analyst. Your role is to perform
a thorough gap analysis between candidate profiles and job requirements.

SCORING CRITERIA (each out of 25, total 100):
1. Skills Match (0-25): How well the candidate's skills align with required skills.
2. Experience Match (0-25): Relevance and depth of professional experience.
3. Education Match (0-25): Educational background fit for the role.
4. Cultural Fit (0-25): Indicators of teamwork, communication, and values alignment.

BIAS MITIGATION GUIDELINES:
- Focus ONLY on skills, qualifications, and demonstrated competencies.
- Do NOT factor in name, gender, age, ethnicity, or personal details.
- Avoid penalizing non-traditional career paths or education.
- Give credit for transferable skills and diverse experiences.

You MUST output valid JSON in this exact format for EACH candidate:
{
  "candidate_id": "...",
  "candidate_name": "...",
  "overall_score": 75.0,
  "skills_match": 20.0,
  "experience_match": 18.0,
  "education_match": 22.0,
  "cultural_fit": 15.0,
  "gaps": ["Missing skill X", "Limited experience in Y"],
  "strengths": ["Strong in A", "Excellent B"],
  "reasoning": "Brief explanation of the scoring rationale..."
}

Return a JSON array of all candidate evaluations."""


def create_screener():
    """Create The Screener agent node function."""

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
    )

    def screener_node(state: RecruitmentState) -> dict:
        """Score each candidate against the job requirements."""

        candidates = state.get("candidates", [])
        job_description = state.get("job_description", "")
        requirements = state.get("requirements", [])

        if not candidates:
            return {
                "error": "No candidates to screen",
                "audit_log": [{
                    "timestamp": datetime.now().isoformat(),
                    "agent": "The Screener",
                    "action": "error",
                    "details": "No candidates available for screening",
                    "stage": PipelineStage.SCREENING.value,
                }],
            }

        # Build candidate summaries
        candidate_summaries = []
        for c in candidates:
            summary = f"""
**Candidate:** {c.get('name', 'Unknown')} (ID: {c.get('id', 'N/A')})
**Skills:** {', '.join(c.get('skills', []))}
**Experience:** {c.get('experience_years', 0)} years
**Education:** {c.get('education', 'Not specified')}
**Resume Summary:** {c.get('resume_text', 'No resume text available')[:500]}
"""
            candidate_summaries.append(summary)

        user_prompt = f"""Evaluate the following candidates against this job description:

## Job Description
{job_description}

## Required Qualifications
{chr(10).join(f'- {r}' for r in requirements)}

## Candidates to Evaluate
{'---'.join(candidate_summaries)}

Score each candidate and return the results as a JSON array.
"""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = llm.invoke(messages)

        # Parse the LLM response
        try:
            # Extract JSON from response
            content = response.content
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            scored_candidates = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            # Fallback: create basic scores
            scored_candidates = []
            for c in candidates:
                scored_candidates.append({
                    "candidate_id": c.get("id", ""),
                    "candidate_name": c.get("name", "Unknown"),
                    "overall_score": c.get("relevance_score", 0.5) * 100,
                    "skills_match": 15.0,
                    "experience_match": 15.0,
                    "education_match": 15.0,
                    "cultural_fit": 15.0,
                    "gaps": ["Automated scoring — manual review recommended"],
                    "strengths": ["Matched by semantic search"],
                    "reasoning": "Fallback scoring based on relevance score.",
                })

        # Sort by overall score descending
        scored_candidates.sort(
            key=lambda x: x.get("overall_score", 0), reverse=True
        )

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "The Screener",
            "action": "scored_candidates",
            "details": f"Scored {len(scored_candidates)} candidates. Top score: {scored_candidates[0].get('overall_score', 0) if scored_candidates else 0}",
            "stage": PipelineStage.SCREENING.value,
        }

        return {
            "scored_candidates": scored_candidates,
            "current_stage": PipelineStage.SHORTLIST_REVIEW.value,
            "shortlist_approval": "pending",
            "audit_log": [audit_entry],
        }

    return screener_node


# ---------------------------------------------------------------------------
# Parallel single-candidate screener (used by the Send API fan-out)
# ---------------------------------------------------------------------------

SINGLE_SYSTEM_PROMPT = """You are an expert HR Screening Analyst. Score exactly ONE candidate
against the given job requirements.

SCORING CRITERIA (each out of 25, total 100):
1. Skills Match (0-25): Alignment with required technical and soft skills.
2. Experience Match (0-25): Relevance and depth of professional experience.
3. Education Match (0-25): Educational background fit for the role.
4. Cultural Fit (0-25): Teamwork, communication, growth mindset indicators.

BIAS MITIGATION: Focus ONLY on competencies. Ignore name, gender, age, ethnicity.

Output EXACTLY this JSON (no markdown, no explanation):
{
  "candidate_id": "...",
  "candidate_name": "...",
  "overall_score": 75.0,
  "skills_match": 20.0,
  "experience_match": 18.0,
  "education_match": 22.0,
  "cultural_fit": 15.0,
  "gaps": ["missing skill X"],
  "strengths": ["excellent Y"],
  "reasoning": "One-sentence rationale."
}"""


def create_screener_single():
    """Create a single-candidate screener node, used in parallel fan-out."""

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
    )

    def screener_single_node(state: dict) -> dict:
        """Score a single candidate. Receives a flat dict from Send API."""
        candidate = state.get("candidate", {})
        job_description = state.get("job_description", "")
        requirements = state.get("requirements", [])
        job_title = state.get("job_title", "")

        # Build a concise candidate summary (section-aware if available)
        sections = candidate.get("sections", {})
        if sections:
            skills_text = sections.get("skills", ", ".join(candidate.get("skills", [])))
            exp_text = sections.get("experience", "")
            edu_text = sections.get("education", candidate.get("education", ""))
        else:
            skills_text = ", ".join(candidate.get("skills", []))
            exp_text = candidate.get("resume_text", "")[:600]
            edu_text = candidate.get("education", "")

        user_prompt = f"""Role: {job_title}

Requirements:
{chr(10).join(f"- {r}" for r in requirements)}

Job Description (excerpt):
{job_description[:500]}

Candidate Profile:
Name: {candidate.get("name", "Unknown")} (ID: {candidate.get("id", "")})
Skills: {skills_text}
Experience ({candidate.get("experience_years", 0)} yrs): {exp_text[:400]}
Education: {edu_text[:200]}

Score this candidate now."""

        messages = [
            SystemMessage(content=SINGLE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        scored = None
        import re
        try:
            response = llm.invoke(messages)
            content = response.content.strip()
            
            # Robust JSON extraction using regex
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                json_str = match.group(0)
                scored = json.loads(json_str)
            else:
                raise ValueError("No JSON object found in LLM response")
        except Exception as e:
            logger.warning(f"Screener JSON extraction failed: {e}")
            # Fallback
            scored = {
                "candidate_id": candidate.get("id", ""),
                "candidate_name": candidate.get("name", "Unknown"),
                "overall_score": round(candidate.get("relevance_score", 0.5) * 80, 1),
                "skills_match": 15.0,
                "experience_match": 15.0,
                "education_match": 12.0,
                "cultural_fit": 12.0,
                "gaps": ["Automated fallback scoring — review manually"],
                "strengths": ["Matched by semantic search"],
                "reasoning": "Fallback: LLM parsing failed.",
            }

        # The fan-in node accumulates these into the main state
        return {"scored_candidates": [scored]}

    return screener_single_node
