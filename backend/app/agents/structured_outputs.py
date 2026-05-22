"""Centralized Pydantic schemas for LLM structured output extraction.

Every agent that calls an LLM and expects structured data uses one of these
schemas with ``ChatOpenAI.with_structured_output()``.  Consolidating them here
avoids duplication, keeps output contracts in one place, and makes it trivial
to add validation or versioning later.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Agent 1 — JD Architect
# ---------------------------------------------------------------------------

class JDArchitectOutput(BaseModel):
    """Structured output from the JD Architect agent."""

    thought_process: str = Field(
        ...,
        description="Strategic reasoning for the JD's tone, structure, and target audience.",
    )
    job_description: str = Field(
        ...,
        description="Complete Markdown-formatted job description with all 7 required sections.",
    )
    bias_audit_summary: str = Field(
        ...,
        description="Summary of the inclusivity audit performed on the JD.",
    )
    identified_biases: list[str] = Field(
        default_factory=list,
        description="List of specific biased terms or phrases that were identified and removed.",
    )


# ---------------------------------------------------------------------------
# Agent 1.5 — JD Critic
# ---------------------------------------------------------------------------

class CritiqueResult(BaseModel):
    """Structured output from the JD Critic agent."""

    score: int = Field(..., ge=1, le=10, description="Quality score from 1 to 10.")
    feedback: str = Field(
        ...,
        description="Specific, actionable feedback on what to fix if score < 9.",
    )
    approved: bool = Field(..., description="True if score >= 9.")
    tone_score: int = Field(
        default=8,
        ge=1,
        le=10,
        description="Sub-score for professional and engaging tone.",
    )
    completeness_score: int = Field(
        default=8,
        ge=1,
        le=10,
        description="Sub-score for mandatory section coverage.",
    )
    inclusivity_score: int = Field(
        default=8,
        ge=1,
        le=10,
        description="Sub-score for inclusive, bias-free language.",
    )


# ---------------------------------------------------------------------------
# Agent 3 — Scout / Reranker
# ---------------------------------------------------------------------------

class RerankerResult(BaseModel):
    """Structured output from the LLM cross-encoder reranker."""

    reason: str = Field(
        ...,
        description="1-2 sentence explanation of why the candidate matches (or doesn't).",
    )
    refined_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Refined match score from 0 to 100.",
    )
    matching_skills: list[str] = Field(
        default_factory=list,
        description="Skills from the JD that the candidate demonstrably has.",
    )
    missing_skills_from_jd: list[str] = Field(
        default_factory=list,
        description="Skills required by the JD that the candidate lacks.",
    )


# ---------------------------------------------------------------------------
# Agent 5 — Outreach
# ---------------------------------------------------------------------------

class OutreachEmailSchema(BaseModel):
    """Structured output from the Outreach agent."""

    subject: str = Field(
        ...,
        description="Enthusiastic, click-worthy email subject line.",
    )
    body: str = Field(
        ...,
        description="Professional email body under 200 words, highly personalized.",
    )


# ---------------------------------------------------------------------------
# Agent 6 — Response Tracker
# ---------------------------------------------------------------------------

class ResponseIntent(str, Enum):
    """Classified intent of a candidate's response."""

    INTERESTED = "interested"
    DECLINED = "declined"
    QUESTIONS_ASKED = "questions_asked"
    RESCHEDULE_REQUEST = "reschedule_request"


class ResponseIntentResult(BaseModel):
    """Structured output from the Response Tracker intent classifier."""

    intent: Literal[
        "interested", "declined", "questions_asked", "reschedule_request"
    ] = Field(
        ...,
        description="Primary intent of the candidate's response.",
    )
    extracted_questions: list[str] = Field(
        default_factory=list,
        description="Specific questions the candidate asked (empty if none).",
    )
    engagement_level: Literal["High", "Medium", "Low"] = Field(
        ...,
        description="Derived engagement level: High (interested), Medium (questions/reschedule), Low (declined).",
    )


# ---------------------------------------------------------------------------
# Agent 7 — Coordinator / Interviewer
# ---------------------------------------------------------------------------

class InterviewAssessmentSchema(BaseModel):
    """Structured output from the interview analysis LLM call."""

    candidate_id: str = Field(..., description="Unique candidate identifier.")
    candidate_name: str = Field(..., description="Candidate's full name.")
    technical_score: float = Field(
        ..., ge=0, le=10, description="Technical competency score (0-10)."
    )
    communication_score: float = Field(
        ..., ge=0, le=10, description="Communication skills score (0-10)."
    )
    problem_solving_score: float = Field(
        ..., ge=0, le=10, description="Problem-solving ability score (0-10)."
    )
    cultural_fit_score: float = Field(
        ..., ge=0, le=10, description="Cultural fit score (0-10)."
    )
    overall_score: float = Field(
        ..., ge=0, le=10, description="Overall interview score (0-10)."
    )
    key_observations: list[str] = Field(
        default_factory=list,
        description="Key strengths or observations from the interview.",
    )
    concerns: list[str] = Field(
        default_factory=list,
        description="Concerns or red flags raised during the interview.",
    )
    transcript_summary: str = Field(
        default="",
        description="Brief summary of the interview transcript.",
    )
