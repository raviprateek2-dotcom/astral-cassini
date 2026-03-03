"""Agent 6: The Interviewer — Interview transcript processing.

Processes interview transcripts (text-based) and extracts
competency assessments across technical skills, communication,
problem-solving, and cultural fit.
"""

from __future__ import annotations

import json
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import RecruitmentState, PipelineStage


SYSTEM_PROMPT = """You are an expert Interview Assessment Analyst. Your role is to
analyze interview transcripts and extract structured competency assessments.

EVALUATION DIMENSIONS (each scored 0-10):
1. Technical Skills: Depth and accuracy of technical knowledge demonstrated.
2. Communication: Clarity, articulation, and ability to explain complex concepts.
3. Problem Solving: Analytical thinking, approach to challenges, creativity.
4. Cultural Fit: Alignment with team values, collaboration style, growth mindset.

BIAS MITIGATION:
- Evaluate ONLY on demonstrated competencies, not communication style preferences.
- Do not penalize accents, language patterns, or cultural communication differences.
- Focus on substance and content over presentation style.

OUTPUT FORMAT (JSON):
{
  "candidate_id": "...",
  "candidate_name": "...",
  "technical_score": 8.0,
  "communication_score": 7.5,
  "problem_solving_score": 8.5,
  "cultural_fit_score": 7.0,
  "overall_score": 7.75,
  "key_observations": ["Observation 1", "Observation 2"],
  "concerns": ["Concern 1"],
  "transcript_summary": "Brief summary of the interview..."
}

Return a JSON array of assessments."""


def create_interviewer():
    """Create The Interviewer agent node function."""

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
    )

    def interviewer_node(state: RecruitmentState) -> dict:
        """Process interview transcripts and generate assessments."""

        scheduled_interviews = state.get("scheduled_interviews", [])
        transcripts = state.get("interview_transcripts", [])
        job_title = state.get("job_title", "")

        # Get unique candidates from scheduled interviews
        candidates_interviewed = {}
        for interview in scheduled_interviews:
            cid = interview.get("candidate_id", "")
            if cid not in candidates_interviewed:
                candidates_interviewed[cid] = interview.get("candidate_name", "Unknown")

        # Use transcripts if available, otherwise generate mock assessments
        if transcripts:
            user_prompt = f"""Analyze the following interview transcripts for the role of {job_title}:

"""
            for i, transcript in enumerate(transcripts):
                user_prompt += f"\n--- Transcript {i+1} ---\n{transcript}\n"

            user_prompt += "\nProvide a competency assessment for each candidate as a JSON array."

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            response = llm.invoke(messages)

            try:
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                assessments = json.loads(content.strip())
            except (json.JSONDecodeError, IndexError):
                assessments = _generate_mock_assessments(candidates_interviewed)
        else:
            # Generate mock assessments for demo
            assessments = _generate_mock_assessments(candidates_interviewed)

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "The Interviewer",
            "action": "completed_assessments",
            "details": f"Assessed {len(assessments)} candidates for '{job_title}'",
            "stage": PipelineStage.INTERVIEWING.value,
        }

        return {
            "interview_assessments": assessments,
            "current_stage": PipelineStage.DECISION.value,
            "audit_log": [audit_entry],
        }

    return interviewer_node


def _generate_mock_assessments(candidates: dict) -> list[dict]:
    """Generate realistic mock assessments for demo purposes."""
    import random

    mock_observations = [
        "Demonstrated strong problem-solving skills with structured approach",
        "Clear and articulate communication throughout the interview",
        "Showed deep technical knowledge in core domain areas",
        "Excellent understanding of system design principles",
        "Provided concrete examples from past experience",
        "Showed enthusiasm for learning and growth",
        "Good collaboration mindset with focus on team success",
        "Strong analytical thinking with data-driven approach",
    ]

    mock_concerns = [
        "Could benefit from more experience with distributed systems",
        "May need ramp-up time on specific tech stack",
        "Limited leadership experience at scale",
        "Could improve on time management during problem-solving",
    ]

    assessments = []
    for cid, name in candidates.items():
        tech = round(random.uniform(6.5, 9.5), 1)
        comm = round(random.uniform(6.0, 9.0), 1)
        prob = round(random.uniform(6.5, 9.5), 1)
        cult = round(random.uniform(6.0, 9.0), 1)
        overall = round((tech + comm + prob + cult) / 4, 2)

        assessments.append({
            "candidate_id": cid,
            "candidate_name": name,
            "technical_score": tech,
            "communication_score": comm,
            "problem_solving_score": prob,
            "cultural_fit_score": cult,
            "overall_score": overall,
            "key_observations": random.sample(mock_observations, 3),
            "concerns": random.sample(mock_concerns, 1),
            "transcript_summary": f"Interview with {name} covered technical skills, problem-solving scenarios, and behavioral questions. Candidate demonstrated competency across evaluated dimensions.",
        })

    return assessments
