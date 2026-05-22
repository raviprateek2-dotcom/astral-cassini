"""Unit tests for the centralized structured output Pydantic schemas.

Validates that all schemas in ``app.agents.structured_outputs`` accept valid
data, reject invalid data, and enforce constraints (ranges, enums, required
fields).
"""

import pytest
from pydantic import ValidationError

from app.agents.structured_outputs import (
    JDArchitectOutput,
    CritiqueResult,
    RerankerResult,
    OutreachEmailSchema,
    ResponseIntentResult,
    InterviewAssessmentSchema,
)


# ---------------------------------------------------------------------------
# JDArchitectOutput
# ---------------------------------------------------------------------------


class TestJDArchitectOutput:
    def test_valid_output(self):
        result = JDArchitectOutput(
            thought_process="Strategic reasoning about tone...",
            job_description="# Senior Engineer\n\n## Role Summary\n...",
            bias_audit_summary="No biased language detected.",
            identified_biases=["Removed 'rockstar' phrasing"],
        )
        assert result.thought_process.startswith("Strategic")
        assert "Senior Engineer" in result.job_description
        assert len(result.identified_biases) == 1

    def test_empty_biases_default(self):
        result = JDArchitectOutput(
            thought_process="...",
            job_description="...",
            bias_audit_summary="Clean.",
        )
        assert result.identified_biases == []

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            JDArchitectOutput(
                thought_process="...",
                # job_description missing
                bias_audit_summary="Clean.",
            )


# ---------------------------------------------------------------------------
# CritiqueResult
# ---------------------------------------------------------------------------


class TestCritiqueResult:
    def test_approved_critique(self):
        result = CritiqueResult(
            score=9,
            feedback="Excellent JD, no changes needed.",
            approved=True,
            tone_score=9,
            completeness_score=10,
            inclusivity_score=9,
        )
        assert result.approved is True
        assert result.score == 9

    def test_rejected_critique(self):
        result = CritiqueResult(
            score=5,
            feedback="Missing Equal Opportunity Statement.",
            approved=False,
        )
        assert result.approved is False
        assert result.score == 5

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            CritiqueResult(score=11, feedback="...", approved=True)

    def test_score_below_minimum(self):
        with pytest.raises(ValidationError):
            CritiqueResult(score=0, feedback="...", approved=False)

    def test_sub_scores_default_values(self):
        result = CritiqueResult(score=7, feedback="...", approved=False)
        assert result.tone_score == 8
        assert result.completeness_score == 8
        assert result.inclusivity_score == 8


# ---------------------------------------------------------------------------
# RerankerResult
# ---------------------------------------------------------------------------


class TestRerankerResult:
    def test_valid_reranker_result(self):
        result = RerankerResult(
            reason="Expert in FastAPI with 5 years experience.",
            refined_score=85,
            matching_skills=["FastAPI", "Python", "SQL"],
            missing_skills_from_jd=["Docker"],
        )
        assert result.refined_score == 85
        assert len(result.matching_skills) == 3
        assert "Docker" in result.missing_skills_from_jd

    def test_score_boundaries(self):
        low = RerankerResult(reason="...", refined_score=0)
        high = RerankerResult(reason="...", refined_score=100)
        assert low.refined_score == 0
        assert high.refined_score == 100

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            RerankerResult(reason="...", refined_score=101)

    def test_empty_skills_default(self):
        result = RerankerResult(reason="...", refined_score=50)
        assert result.matching_skills == []
        assert result.missing_skills_from_jd == []


# ---------------------------------------------------------------------------
# OutreachEmailSchema
# ---------------------------------------------------------------------------


class TestOutreachEmailSchema:
    def test_valid_email(self):
        result = OutreachEmailSchema(
            subject="Exciting Opportunity at PRO HR: ML Engineer",
            body="Hi Priya, we noticed your ML expertise...",
        )
        assert "ML Engineer" in result.subject
        assert "Priya" in result.body

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            OutreachEmailSchema(subject="Only subject")  # body missing


# ---------------------------------------------------------------------------
# ResponseIntentResult
# ---------------------------------------------------------------------------


class TestResponseIntentResult:
    def test_interested_response(self):
        result = ResponseIntentResult(
            intent="interested",
            extracted_questions=[],
            engagement_level="High",
        )
        assert result.intent == "interested"
        assert result.engagement_level == "High"

    def test_questions_asked(self):
        result = ResponseIntentResult(
            intent="questions_asked",
            extracted_questions=["What is the remote policy?", "What is the team size?"],
            engagement_level="Medium",
        )
        assert len(result.extracted_questions) == 2
        assert result.engagement_level == "Medium"

    def test_declined(self):
        result = ResponseIntentResult(
            intent="declined",
            extracted_questions=[],
            engagement_level="Low",
        )
        assert result.intent == "declined"

    def test_invalid_intent(self):
        with pytest.raises(ValidationError):
            ResponseIntentResult(
                intent="maybe_later",  # invalid
                extracted_questions=[],
                engagement_level="High",
            )

    def test_invalid_engagement_level(self):
        with pytest.raises(ValidationError):
            ResponseIntentResult(
                intent="interested",
                extracted_questions=[],
                engagement_level="Very High",  # invalid
            )


# ---------------------------------------------------------------------------
# InterviewAssessmentSchema
# ---------------------------------------------------------------------------


class TestInterviewAssessmentSchema:
    def test_valid_assessment(self):
        result = InterviewAssessmentSchema(
            candidate_id="cand-001",
            candidate_name="Priya Sharma",
            technical_score=8.5,
            communication_score=7.0,
            problem_solving_score=9.0,
            cultural_fit_score=8.0,
            overall_score=8.1,
            key_observations=["Strong system design skills"],
            concerns=["Limited cloud experience"],
            transcript_summary="Performed well overall.",
        )
        assert result.technical_score == 8.5
        assert len(result.concerns) == 1

    def test_score_boundary_zero(self):
        result = InterviewAssessmentSchema(
            candidate_id="cand-002",
            candidate_name="Test",
            technical_score=0,
            communication_score=0,
            problem_solving_score=0,
            cultural_fit_score=0,
            overall_score=0,
        )
        assert result.overall_score == 0

    def test_score_boundary_ten(self):
        result = InterviewAssessmentSchema(
            candidate_id="cand-003",
            candidate_name="Test",
            technical_score=10,
            communication_score=10,
            problem_solving_score=10,
            cultural_fit_score=10,
            overall_score=10,
        )
        assert result.overall_score == 10

    def test_score_exceeds_max(self):
        with pytest.raises(ValidationError):
            InterviewAssessmentSchema(
                candidate_id="cand-004",
                candidate_name="Test",
                technical_score=11,  # invalid
                communication_score=8,
                problem_solving_score=8,
                cultural_fit_score=8,
                overall_score=8,
            )
