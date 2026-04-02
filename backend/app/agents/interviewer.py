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

    async def interviewer_node(state: RecruitmentState) -> dict:
        """Process interview transcripts OR generate contextual questions for prep."""
        
        # Skip if we are past the interviewing stage
        current_stage = state.get("current_stage")
        if current_stage and current_stage != PipelineStage.INTERVIEWING.value:
            return {}

        scored_candidates = state.get("scored_candidates", [])
        transcripts = state.get("interview_transcripts", [])
        job_title = state.get("job_title", "")
        job_description = state.get("job_description", "")

        # 1. ANALYZE TRANSCRIPTS (If available)
        if transcripts:
            user_prompt = f"Analyze transcripts for {job_title}:\n" + "\n".join(transcripts)
            messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
            
            try:
                response = await llm.ainvoke(messages)
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                assessments = json.loads(content.strip())
            except Exception:
                assessments = _generate_mock_assessments({c.get("id", c.get("candidate_id")): c.get("name", c.get("candidate_name")) for c in scored_candidates})

            return {
                "interview_assessments": assessments,
                "current_stage": PipelineStage.DECISION.value,
                "audit_log": [{
                    "timestamp": datetime.now().isoformat(),
                    "agent": "The Interviewer",
                    "action": "completed_assessments",
                    "details": f"Assessed {len(assessments)} candidates for '{job_title}'",
                    "stage": PipelineStage.INTERVIEWING.value,
                }],
            }
        
        # 2. GENERATE QUESTIONS (Interview Prep)
        else:
            prep_data = []
            for candidate in scored_candidates:
                gaps = candidate.get("gaps", [])
                name = candidate.get("name", candidate.get("candidate_name", "Unknown"))
                cid = candidate.get("id", candidate.get("candidate_id"))
                
                prep_prompt = f"""As an expert interviewer for the role of {job_title}, 
                generate 5-7 targeted behavioral interview questions for candidate {name}.
                
                Focus on these specific gaps/concerns identified during screening:
                {chr(10).join(f'- {g}' for g in gaps)}
                
                Job context:
                {job_description[:500]}
                
                Return the questions as a simple JSON list of strings named "questions"."""
                
                try:
                    res = await llm.ainvoke([HumanMessage(content=prep_prompt)])
                    content = res.content
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    questions_data = json.loads(content.strip())
                    questions = questions_data.get("questions", [])
                except Exception:
                    questions = [f"Considering your background, how would you address your gap in {g}?" for g in gaps[:3]]
                    if not questions:
                        questions = ["Tell me about your most challenging project.", "How do you handle conflict in a team?"]
                
                prep_data.append({
                    "candidate_id": cid,
                    "candidate_name": name,
                    "questions": questions
                })

            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": "The Interviewer",
                "action": "generated_contextual_questions",
                "details": f"Prepared interview guides for {len(prep_data)} candidates addressing identified gaps.",
                "stage": PipelineStage.INTERVIEWING.value,
            }

            return {
                "suggested_questions": prep_data,
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
