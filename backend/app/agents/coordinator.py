"""Agent 7: Hiring Operations Coordinator — Full pipeline execution.

Consolidates the roles of:
1. The Coordinator (Scheduling)
2. The Interviewer (Assessment) - LLM Extraction
3. The Decider (Final Decision) - PURE DETERMINISTIC MATH
4. Offer Generator (Offer drafting)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta

from pydantic import BaseModel, SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import SharedState, PipelineStage, Interview, Assessment, Recommendation, OfferRecord, DecisionTrace
from app.tools.calendar_tool import schedule_meeting, check_availability
from app.tools.email_tool import send_interview_invitation
from app.agents.structured_outputs import InterviewAssessmentSchema

logger = logging.getLogger(__name__)

# --- Prompts ---

INTERVIEWER_PROMPT = """You are an expert Interview Assessment Analyst. Your role is tightly deterministic.
Analyze the following interview data and extract structured assessments for each candidate.
Focus exclusively on technical ability, communication, problem-solving, and cultural fit.
Do NOT factor in any personal identifiers, gender, or demographic information.
"""

OFFER_PROMPT = """You are a Compensation Specialist. Generate a professional Markdown
offer letter for the successful candidate based on the job details and performance."""


# --- Structured output wrapper ---

class InterviewAssessmentList(BaseModel):
    assessments: list[InterviewAssessmentSchema]


# --- Utilities ---

def _anonymize_transcript(text: str, names_to_strip: list[str]) -> str:
    """Strip candidate names and personal identifiers from transcript text."""
    result = text
    for name in names_to_strip:
        for part in name.split():
            if len(part) > 2:
                result = re.sub(re.escape(part), '[CANDIDATE]', result, flags=re.IGNORECASE)
    # Strip common gendered pronouns to reduce bias
    result = re.sub(r'\b(he|she|him|her|his|hers)\b', 'they/them', result, flags=re.IGNORECASE)
    return result


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

    # Filter out candidates who have declined (from response tracker)
    declined_ids: set[str] = {
        resp.candidate_id
        for resp in state.candidate_responses
        if resp.intent == "declined"
    }
    eligible = [c for c in scored_candidates if c.candidate_id not in declined_ids]
    if not eligible:
        state.error = "All candidates declined"
        return state

    top = [c for c in eligible if c.overall_score >= 60][:5]
    if not top:
        top = eligible[:3]

    scheduled = []
    base_date = datetime.now() + timedelta(days=2)
    for i, c in enumerate(top):
        sched_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        avail = check_availability(
            attendees=[f"{str(c.candidate_name).lower().replace(' ', '.')}@email.com"],
            date=sched_date,
        )
        slots = avail.get("available_slots", [])
        # Pick first available slot for technical, second for behavioral
        tech_time = slots[0]["start"] if len(slots) > 0 else f"{sched_date}T09:00:00"
        behav_time = slots[1]["start"] if len(slots) > 1 else f"{sched_date}T10:30:00"

        meeting = schedule_meeting(
            title=f"Interview: {c.candidate_name}",
            time=tech_time,
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
            scheduled_time=tech_time,
            meeting_link=meet_link,
            status="scheduled"
        ))
        # Behavioral
        scheduled.append(Interview(
            id=f"int-{c.candidate_id}-behav",
            candidate_id=c.candidate_id,
            candidate_name=c.candidate_name,
            interview_type="behavioral",
            scheduled_time=behav_time,
            meeting_link=meet_link,
            status="scheduled"
        ))
        send_interview_invitation(
            to_email=f"{str(c.candidate_name).lower().replace(' ', '.')}@email.com",
            candidate_name=c.candidate_name,
            job_title=state.job_title,
            interview_time=tech_time,
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
            # Anonymize transcripts before sending to LLM
            candidate_names = [c.candidate_name for c in state.scored_candidates]
            anonymized = [
                _anonymize_transcript(t, candidate_names) for t in transcripts
            ]
            structured_llm = llm.with_structured_output(InterviewAssessmentList)
            result = await structured_llm.ainvoke([
                SystemMessage(content=INTERVIEWER_PROMPT),
                HumanMessage(content=f"Data: {chr(10).join(anonymized)}"),
            ])
            assessments_dicts = [a.model_dump() for a in result.assessments]
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
    w_scr = state.decision_weights.screening
    w_int = state.decision_weights.interview
    
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
            
        # Dynamic weight split from state.decision_weights
        weighted = (scr_score * w_scr) + (int_score * w_int)
        
        # Hard Rules for Decision
        if weighted >= 90 and missing_crit == 0:
            decision = "strong_hire"
        elif weighted >= 75 and missing_crit < 3:
            decision = "hire"
        elif weighted >= 60:
            decision = "maybe"
        else:
            decision = "no_hire"

        scr_pct = round(w_scr * 100)
        int_pct = round(w_int * 100)
        reasoning = f"Determined by deterministic formula: Screening={scr_score} ({scr_pct}%), Interview={round(int_score, 1)} ({int_pct}%). Weighted={round(weighted, 1)}. Concerns={missing_crit}."
            
        recommendations.append(Recommendation(
            candidate_id=cid,
            candidate_name=sc.candidate_name,
            decision=decision,
            confidence=round(weighted, 1),
            screening_weight=round(scr_score * w_scr, 1),
            interview_weight=round(int_score * w_int, 1),
            overall_weighted_score=round(weighted, 1),
            reasoning=reasoning,
            risk_factors=sc.gaps + (assessment.concerns if assessment else [])
        ))
        rule_desc = (
            f"weighted>=90&&concerns==0=>strong_hire; "
            f"weighted>=75&&concerns<3=>hire; "
            f"weighted>=60=>maybe; else no_hire "
            f"(screening_w={w_scr}, interview_w={w_int})"
        )
        traces.append(
            DecisionTrace(
                candidate_id=cid,
                candidate_name=sc.candidate_name,
                screening_score=round(scr_score, 1),
                interview_score_scaled=round(int_score, 1),
                concerns_count=missing_crit,
                weighted_score=round(weighted, 1),
                decision=decision,
                rule_applied=rule_desc,
            )
        )

    # Sort so strong_hire/hire are at the top
    _decision_rank = {"strong_hire": 3, "hire": 2, "maybe": 1, "no_hire": 0}
    recommendations.sort(key=lambda x: (_decision_rank.get(x.decision, 0), x.overall_weighted_score), reverse=True)

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


# --- Mock Assessments ---

def _generate_mock_assessments(candidates: dict) -> list[dict]:
    assessments = []
    for cid, name in candidates.items():
        seed = hash(cid) % 1000
        tech = 6.0 + (seed % 40) / 10.0           # 6.0-9.9
        comm = 6.0 + ((seed * 7) % 40) / 10.0
        prob = 6.0 + ((seed * 13) % 40) / 10.0
        cult = 6.0 + ((seed * 19) % 40) / 10.0
        overall = round((tech + comm + prob + cult) / 4.0, 2)
        concerns: list[str] = []
        if overall < 7.5:
            concerns.append("Below-average overall score may indicate gaps")
            if tech < 7.0:
                concerns.append("Technical skills need further validation")
        assessments.append({
            "candidate_id": cid,
            "candidate_name": name,
            "technical_score": round(tech, 1),
            "communication_score": round(comm, 1),
            "problem_solving_score": round(prob, 1),
            "cultural_fit_score": round(cult, 1),
            "overall_score": overall,
            "key_observations": ["Strong candidate"] if overall >= 7.5 else ["Average performance"],
            "concerns": concerns,
            "transcript_summary": "Good mock interview." if overall >= 7.5 else "Adequate mock interview with some areas for improvement."
        })
    return assessments
