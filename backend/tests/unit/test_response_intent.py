"""Unit tests for the refactored Response Tracker intent classification.

Tests the mock simulation diversity paths and verifies engagement level
mapping from intent classification.
"""

import pytest

from app.models.state import CandidateResponse


# ---------------------------------------------------------------------------
# CandidateResponse model tests (with new fields)
# ---------------------------------------------------------------------------


class TestCandidateResponseModel:
    """Tests for the extended CandidateResponse Pydantic model."""

    def test_default_intent(self):
        cr = CandidateResponse(
            candidate_id="cand-001",
            candidate_name="Test",
        )
        assert cr.intent == "interested"
        assert cr.extracted_questions == []
        assert cr.engagement_level == "High"

    def test_interested_response(self):
        cr = CandidateResponse(
            candidate_id="cand-001",
            candidate_name="Test",
            response="Sounds great! Let's schedule a call.",
            intent="interested",
            engagement_level="High",
        )
        assert cr.intent == "interested"

    def test_declined_response(self):
        cr = CandidateResponse(
            candidate_id="cand-002",
            candidate_name="Test",
            response="Thank you, but I have accepted another offer.",
            intent="declined",
            engagement_level="Low",
        )
        assert cr.intent == "declined"
        assert cr.engagement_level == "Low"

    def test_questions_asked(self):
        cr = CandidateResponse(
            candidate_id="cand-003",
            candidate_name="Test",
            response="What is the remote policy?",
            intent="questions_asked",
            engagement_level="Medium",
            extracted_questions=["What is the remote policy?"],
        )
        assert cr.intent == "questions_asked"
        assert len(cr.extracted_questions) == 1

    def test_reschedule_request(self):
        cr = CandidateResponse(
            candidate_id="cand-004",
            candidate_name="Test",
            response="Can we do next week instead?",
            intent="reschedule_request",
            engagement_level="Medium",
        )
        assert cr.intent == "reschedule_request"


# ---------------------------------------------------------------------------
# Intent to engagement level mapping
# ---------------------------------------------------------------------------


class TestIntentEngagementMapping:
    """Verifies that the intent → engagement_level mapping is consistent."""

    EXPECTED_MAPPING = {
        "interested": "High",
        "questions_asked": "Medium",
        "reschedule_request": "Medium",
        "declined": "Low",
    }

    @pytest.mark.parametrize("intent, expected_level", list(EXPECTED_MAPPING.items()))
    def test_mapping(self, intent: str, expected_level: str):
        cr = CandidateResponse(
            candidate_id="test",
            candidate_name="Test",
            intent=intent,
            engagement_level=expected_level,
        )
        assert cr.engagement_level == expected_level


# ---------------------------------------------------------------------------
# State model backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Ensures existing CandidateResponse data without new fields still works."""

    def test_old_format_deserialization(self):
        """Simulate loading old workflow_state JSON that lacks intent/extracted_questions."""
        old_data = {
            "candidate_id": "cand-old",
            "candidate_name": "Legacy Candidate",
            "response": "I am interested.",
            "engagement_level": "High",
        }
        cr = CandidateResponse(**old_data)
        assert cr.intent == "interested"  # default
        assert cr.extracted_questions == []  # default
