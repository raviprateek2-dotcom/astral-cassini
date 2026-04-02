"""Agent 7: The Decider — Final hire/no-hire recommendation.

Aggregates all signals (screening scores, interview assessments,
gap analysis) and produces a final recommendation with confidence
scores and explainable reasoning.
"""

from __future__ import annotations

import json
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import RecruitmentState, PipelineStage


SYSTEM_PROMPT = """You are the Final Decision Analyst for a recruitment pipeline. Your
role is to aggregate ALL available signals and produce a clear hire/no-hire/maybe
recommendation for each candidate.

INPUT SIGNALS:
1. Screening Scores (from The Screener): Skills match, experience, education, cultural fit
2. Interview Assessments (from The Interviewer): Technical, communication, problem-solving, cultural fit
3. Gap Analysis: Identified gaps and strengths

DECISION CRITERIA:
- HIRE: Overall weighted score >= 75 AND no critical gaps AND interview score >= 7.0
- MAYBE: Overall weighted score 60-74 OR minor concerns that need further evaluation
- NO HIRE: Overall weighted score < 60 OR critical disqualifying gaps

WEIGHTING:
- Screening Score: 40% weight
- Interview Assessment: 60% weight

BIAS MITIGATION:
- Base decisions ONLY on demonstrated competencies and qualifications.
- Provide explainable reasoning for every recommendation.
- Flag any potential bias risks in your reasoning.

OUTPUT FORMAT (JSON array):
[{
  "candidate_id": "...",
  "candidate_name": "...",
  "decision": "hire|no_hire|maybe",
  "confidence": 85.0,
  "screening_weight": 32.0,
  "interview_weight": 48.0,
  "overall_weighted_score": 80.0,
  "reasoning": "Detailed explanation...",
  "risk_factors": ["Risk 1", "Risk 2"]
}]"""


def create_decider():
    """Create The Decider agent node function."""

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.1,
        api_key=settings.openai_api_key,
    )

    def decider_node(state: RecruitmentState) -> dict:
        """Evaluate all data to make final hiring recommendations."""
        
        # Skip if we are past the decision stage
        current_stage = state.get("current_stage")
        if current_stage and current_stage != PipelineStage.DECISION.value:
            return {}

        scored_candidates = state.get("scored_candidates", [])
        assessments = state.get("interview_assessments", [])
        job_title = state.get("job_title", "")

        if not scored_candidates and not assessments:
            return {
                "error": "Insufficient data for decision making",
                "audit_log": [{
                    "timestamp": datetime.now().isoformat(),
                    "agent": "The Decider",
                    "action": "error",
                    "details": "No screening or interview data available",
                    "stage": PipelineStage.DECISION.value,
                }],
            }

        # Build assessment lookup
        assessment_map = {a.get("candidate_id", ""): a for a in assessments}

        user_prompt = f"""Make final hiring recommendations for the role of **{job_title}**.

## Screening Scores
"""
        for sc in scored_candidates:
            user_prompt += f"""
**{sc.get('candidate_name', 'Unknown')}** (ID: {sc.get('candidate_id', '')})
- Overall Score: {sc.get('overall_score', 0)}/100
- Skills: {sc.get('skills_match', 0)}/25 | Experience: {sc.get('experience_match', 0)}/25
- Education: {sc.get('education_match', 0)}/25 | Cultural Fit: {sc.get('cultural_fit', 0)}/25
- Strengths: {', '.join(sc.get('strengths', []))}
- Gaps: {', '.join(sc.get('gaps', []))}
"""

        user_prompt += "\n## Interview Assessments\n"
        for sc in scored_candidates:
            cid = sc.get("candidate_id", "")
            a = assessment_map.get(cid)
            if a:
                user_prompt += f"""
**{a.get('candidate_name', 'Unknown')}** (ID: {cid})
- Technical: {a.get('technical_score', 0)}/10 | Communication: {a.get('communication_score', 0)}/10
- Problem Solving: {a.get('problem_solving_score', 0)}/10 | Cultural Fit: {a.get('cultural_fit_score', 0)}/10
- Overall Interview: {a.get('overall_score', 0)}/10
- Key Observations: {', '.join(a.get('key_observations', []))}
- Concerns: {', '.join(a.get('concerns', []))}
"""

        user_prompt += "\nProvide your final recommendations as a JSON array."

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
            recommendations = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            # Fallback: compute recommendations manually
            recommendations = _compute_fallback_recommendations(
                scored_candidates, assessment_map
            )

        # Sort by confidence descending
        recommendations.sort(
            key=lambda x: x.get("confidence", 0), reverse=True
        )

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "The Decider",
            "action": "final_recommendations",
            "details": f"Produced {len(recommendations)} recommendations. "
                       f"Hire: {sum(1 for r in recommendations if r.get('decision') == 'hire')}, "
                       f"Maybe: {sum(1 for r in recommendations if r.get('decision') == 'maybe')}, "
                       f"No Hire: {sum(1 for r in recommendations if r.get('decision') == 'no_hire')}",
            "stage": PipelineStage.DECISION.value,
        }

        return {
            "final_recommendations": recommendations,
            "current_stage": PipelineStage.HIRE_REVIEW.value,
            "hire_approval": "pending",
            "audit_log": [audit_entry],
        }

    return decider_node


def _compute_fallback_recommendations(
    scored_candidates: list[dict],
    assessment_map: dict[str, dict],
) -> list[dict]:
    """Compute recommendations without LLM as fallback."""
    recommendations = []
    for sc in scored_candidates:
        cid = sc.get("candidate_id", "")
        screening_score = sc.get("overall_score", 0)
        assessment = assessment_map.get(cid, {})
        interview_score = assessment.get("overall_score", 5.0) * 10  # scale to 100

        # 40% screening + 60% interview
        weighted = (screening_score * 0.4) + (interview_score * 0.6)

        if weighted >= 75:
            decision = "hire"
            confidence = min(95, weighted)
        elif weighted >= 60:
            decision = "maybe"
            confidence = weighted
        else:
            decision = "no_hire"
            confidence = 100 - weighted

        recommendations.append({
            "candidate_id": cid,
            "candidate_name": sc.get("candidate_name", "Unknown"),
            "decision": decision,
            "confidence": round(confidence, 1),
            "screening_weight": round(screening_score * 0.4, 1),
            "interview_weight": round(interview_score * 0.6, 1),
            "overall_weighted_score": round(weighted, 1),
            "reasoning": f"Weighted score: {weighted:.1f} (screening {screening_score:.0f}×0.4 + interview {interview_score:.0f}×0.6)",
            "risk_factors": sc.get("gaps", []),
        })

    return recommendations
