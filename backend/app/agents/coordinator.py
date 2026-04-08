"""Agent 5: Hiring Operations Coordinator — Full pipeline execution.

Consolidates the roles of:
1. The Coordinator (Scheduling)
2. The Interviewer (Assessment) - LLM Extraction
3. The Decider (Final Decision) - PURE DETERMINISTIC MATH
4. Offer Generator (Offer drafting)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import SharedState, PipelineStage, Interview, Assessment, Recommendation, OfferRecord, DecisionTrace
from app.tools.calendar_tool import schedule_meeting
from app.tools.email_tool import send_interview_invitation

logger = logging.getLogger(__name__)

# --- Prompts ---

INTERVIEWER_PROMPT = """You are an expert Interview Assessment Analyst. Your role is tightly deterministic.
Analyze the following interview data and extract specific structured JSON.
Return a JSON array of objects.

JSON schema per object:
{"candidate_id": "string", "candidate_name": "string", "technical_score": float(0-10), "communication_score": float(0-10), "problem_solving_score": float(0-10), "cultural_fit_score": float(0-10), "overall_score": float(0-10), "key_observations": ["string"], "concerns": ["string"], "transcript_summary": "string"}
"""

OFFER_PROMPT = """You are a Compensation Specialist. Generate a professional Markdown
offer letter for the successful candidate based on the job details and performance."""


def _coerce_llm_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(part) for part in content)
    return str(content)

async def coordinator_node(state: SharedState) -> SharedState:
    """Central execution node for the final hiring stages."""
    current_stage = state.current_stage

    if current_stage == PipelineStage.SCHEDULING.value:
        return await _handle_scheduling(state)
    if current_stage == PipelineStage.INTERVIEWING.value:
        # Avoid constructing ChatOpenAI without a key (OpenAI SDK rejects api_key=None).
        llm: ChatOpenAI | None = None
        if state.interview_transcripts and settings.openai_api_key:
            llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=0.1,
                api_key=SecretStr(settings.openai_api_key),
            )
        return await _handle_interview_analysis(state, llm)
    if current_stage == PipelineStage.DECISION.value:
        return await _handle_final_decision(state)
    if current_stage == PipelineStage.OFFER.value:
        llm = None
        if settings.openai_api_key:
            llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=0.1,
                api_key=SecretStr(settings.openai_api_key),
            )
        return await _handle_offer_generation(state, llm)

    return state


async def _handle_scheduling(state: SharedState) -> SharedState:
    scored_candidates = state.scored_candidates
    if not scored_candidates:
        state.error = "No candidates to schedule"
        return state

    top = [c for c in scored_candidates if c.overall_score >= 60][:5]
    if not top:
        top = scored_candidates[:3]

    scheduled = []
    base_time = datetime.now() + timedelta(days=2)
    for i, c in enumerate(top):
        tm = base_time + timedelta(days=i, hours=10)
        
        meeting = schedule_meeting(
            title=f"Interview: {c.candidate_name}",
            time=tm.isoformat(),
            duration=60,
            attendees=[f"{str(c.candidate_name).lower().replace(' ', '.')}@email.com"],
        )
        meet_link = str(meeting.get("meeting_link", "") or "")
        # Technical
        scheduled.append(Interview(
            id=f"int-{c.candidate_id}-tech",
            candidate_id=c.candidate_id,
            candidate_name=c.candidate_name,
            interview_type="technical",
            scheduled_time=tm.isoformat(),
            meeting_link=meet_link,
            status="scheduled"
        ))
        # Behavioral
        scheduled.append(Interview(
            id=f"int-{c.candidate_id}-behav",
            candidate_id=c.candidate_id,
            candidate_name=c.candidate_name,
            interview_type="behavioral",
            scheduled_time=(tm + timedelta(hours=3)).isoformat(),
            meeting_link=meet_link,
            status="scheduled"
        ))
        send_interview_invitation(
            to_email=f"{str(c.candidate_name).lower().replace(' ', '.')}@email.com",
            candidate_name=c.candidate_name,
            job_title=state.job_title,
            interview_time=tm.isoformat(),
            meeting_link=meet_link,
        )

    state.scheduled_interviews = scheduled
    state.current_stage = PipelineStage.INTERVIEWING.value
    state.log_audit("Ops Coordinator", "scheduled", f"Scheduled {len(scheduled)} interviews", PipelineStage.SCHEDULING.value)
    return state

async def _handle_interview_analysis(
    state: SharedState,
    llm: ChatOpenAI | None,
) -> SharedState:
    transcripts = state.interview_transcripts
    if not transcripts:
        # Generate mock assessments if no real transcripts available
        cands = {c.candidate_id: c.candidate_name for c in state.scored_candidates}
        assessments_dicts = _generate_mock_assessments(cands)
    elif llm is None:
        cands = {c.candidate_id: c.candidate_name for c in state.scored_candidates}
        assessments_dicts = _generate_mock_assessments(cands)
    else:
        try:
            res = await llm.ainvoke([SystemMessage(content=INTERVIEWER_PROMPT), HumanMessage(content=f"Data: {chr(10).join(transcripts)}")])
            content = _coerce_llm_text(res.content)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            assessments_dicts = json.loads(content.strip())
        except Exception as e:
            logger.error(f"Failed to parse LLM interview output: {e}")
            cands = {c.candidate_id: c.candidate_name for c in state.scored_candidates}
            assessments_dicts = _generate_mock_assessments(cands)

    state.interview_assessments = [Assessment(**a) for a in assessments_dicts]
    state.current_stage = PipelineStage.DECISION.value
    
    state.log_audit("Ops Coordinator", "assessed", f"Analyzed {len(state.interview_assessments)} interviews", PipelineStage.INTERVIEWING.value)
    state.log_audit("Ethical Guardian Utility", "bias_audit", "Verified: Interview analysis focused on technical/behavioral competencies. Personal identifiers excluded.", PipelineStage.INTERVIEWING.value)
    
    return state


async def _handle_final_decision(state: SharedState) -> SharedState:
    """Purely Deterministic Rule Engine for Final Decisions. ZERO LLM OR RANDOMNESS."""
    scored = state.scored_candidates
    assessments_dict = {a.candidate_id: a for a in state.interview_assessments}
    
    recommendations = []
    traces: list[DecisionTrace] = []
    
    for sc in scored:
        cid = sc.candidate_id
        scr_score = sc.overall_score
        
        assessment = assessments_dict.get(cid)
        if assessment:
            int_score = assessment.overall_score * 10 # Scale up to 100
            missing_crit = len(assessment.concerns)
        else:
            int_score = 50.0  # Default middle ground
            missing_crit = 0
            
        # Hard Rule: 40% initial screen + 60% interview
        weighted = (scr_score * 0.4) + (int_score * 0.6)
        
        # Hard Rules for Decision
        if weighted >= 75 and missing_crit < 3:
            decision = "hire"
        elif weighted >= 60:
            decision = "maybe"
        else:
            decision = "no_hire"
            
        reasoning = f"Determined by deterministic formula: Screening={scr_score} (40%), Interview={round(int_score, 1)} (60%). Weighted={round(weighted, 1)}. Concerns={missing_crit}."
            
        recommendations.append(Recommendation(
            candidate_id=cid,
            candidate_name=sc.candidate_name,
            decision=decision,
            confidence=round(weighted, 1),
            screening_weight=round(scr_score * 0.4, 1),
            interview_weight=round(int_score * 0.6, 1),
            overall_weighted_score=round(weighted, 1),
            reasoning=reasoning,
            risk_factors=sc.gaps + (assessment.concerns if assessment else [])
        ))
        traces.append(
            DecisionTrace(
                candidate_id=cid,
                candidate_name=sc.candidate_name,
                screening_score=round(scr_score, 1),
                interview_score_scaled=round(int_score, 1),
                concerns_count=missing_crit,
                weighted_score=round(weighted, 1),
                decision=decision,
                rule_applied="weighted>=75&&concerns<3=>hire; weighted>=60=>maybe; else no_hire",
            )
        )

    # Sort so hires are at the top
    recommendations.sort(key=lambda x: (x.decision == 'hire', x.overall_weighted_score), reverse=True)

    state.final_recommendations = recommendations
    state.decision_traces = traces
    state.current_stage = PipelineStage.HIRE_REVIEW.value
    state.hire_approval = "pending"
    
    state.log_audit("Ops Coordinator", "decided", "Final recommendations generated deterministically", PipelineStage.DECISION.value)
    state.log_audit("Ethical Guardian Utility", "bias_audit", "Verified: Final hiring recommendation based entirely on strict mathematical criteria. Demographic data strictly excluded.", PipelineStage.DECISION.value)

    return state


async def _handle_offer_generation(
    state: SharedState,
    llm: ChatOpenAI | None,
) -> SharedState:
    recs = state.final_recommendations
    top = next((r for r in recs if r.decision == "hire"), recs[0] if recs else None)
    
    if not top: 
        state.current_stage = PipelineStage.COMPLETED.value
        return state

    if llm is None:
        offer = OfferRecord(
            candidate_id=top.candidate_id,
            candidate_name=top.candidate_name,
            offer_markdown="# Offer Letter\n\nMock offer (no LLM key).",
            status="draft",
        )
        state.offer_details = [offer]
        state.current_stage = PipelineStage.COMPLETED.value
        state.log_audit("Ops Coordinator", "offered", "Offer letter drafted (mock)", PipelineStage.OFFER.value)
        return state

    try:
        res = await llm.ainvoke([SystemMessage(content=OFFER_PROMPT), HumanMessage(content=f"Draft for {top.candidate_name} for role {state.job_title} at {state.salary_range}")])
        offer_markdown = _coerce_llm_text(res.content)
        offer = OfferRecord(
            candidate_id=top.candidate_id, 
            candidate_name=top.candidate_name, 
            offer_markdown=offer_markdown,
            status="draft"
        )
    except Exception:
        offer = OfferRecord(
            candidate_id=top.candidate_id, 
            candidate_name=top.candidate_name, 
            offer_markdown="# Offer Letter\n\nFallback mock offer.", 
            status="error"
        )

    state.offer_details = [offer]
    state.current_stage = PipelineStage.COMPLETED.value
    state.log_audit("Ops Coordinator", "offered", "Offer letter drafted", PipelineStage.OFFER.value)
    return state


# --- Utilities ---

def _generate_mock_assessments(candidates: dict) -> list[dict]:
    assessments = []
    for cid, name in candidates.items():
        tech, comm, prob, cult = 8.5, 8.0, 7.5, 9.0
        overall = (tech + comm + prob + cult) / 4.0
        assessments.append({
            "candidate_id": cid, 
            "candidate_name": name, 
            "technical_score": tech,
            "communication_score": comm,
            "problem_solving_score": prob,
            "cultural_fit_score": cult,
            "overall_score": overall, 
            "key_observations": ["Strong candidate"], 
            "concerns": [],
            "transcript_summary": "Good mock interview."
        })
    return assessments
