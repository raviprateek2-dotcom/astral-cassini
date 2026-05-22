"""Unit tests for the refactored Screener agent scoring logic.

Tests dynamic experience scoring, synonym-based skill matching,
education field alignment, and cultural fit proximity bonuses.
"""

import pytest
import asyncio

from app.models.state import SharedState, PipelineStage, CandidateProfile, ScoredCandidate


# ---------------------------------------------------------------------------
# Helper: build a candidate and score them
# ---------------------------------------------------------------------------


def _make_candidate(
    name: str = "Test Candidate",
    skills: list[str] | None = None,
    experience_years: int = 5,
    education: str = "B.Tech in Computer Science",
) -> CandidateProfile:
    return CandidateProfile(
        id=f"cand-{name.lower().replace(' ', '-')}",
        name=name,
        email=f"{name.lower().replace(' ', '.')}@test.com",
        skills=skills or ["Python", "SQL"],
        experience_years=experience_years,
        education=education,
        resume_text=f"Experienced professional with {experience_years} years.",
    )


def _build_state(
    candidates: list[CandidateProfile],
    requirements: list[str] | None = None,
    target_exp: int = 5,
) -> SharedState:
    return SharedState(
        job_id="test-job",
        job_title="ML Engineer",
        department="Engineering",
        requirements=requirements or ["Python", "Machine Learning", "SQL"],
        candidates=candidates,
        target_experience_years=target_exp,
        current_stage=PipelineStage.SCREENING.value,
    )


# ---------------------------------------------------------------------------
# Scoring tests (run the actual screener_node)
# ---------------------------------------------------------------------------


class TestScreenerScoring:
    """End-to-end scoring tests via screener_node()."""

    @pytest.fixture(autouse=True)
    def _import_screener(self):
        from app.agents.screener import screener_node, _score_candidate
        self.screener_node = screener_node
        self._score_candidate = _score_candidate

    def test_perfect_skill_match(self):
        """Candidate with all required skills should max out skills_match."""
        cand = _make_candidate(
            skills=["Python", "Machine Learning", "SQL"],
            experience_years=5,
        )
        state = _build_state([cand], requirements=["Python", "Machine Learning", "SQL"])
        result = asyncio.run(self.screener_node(state))
        scored = result.scored_candidates[0]
        assert scored.skills_match == 25.0, f"Expected 25.0, got {scored.skills_match}"

    def test_synonym_skill_matching(self):
        """'Postgres' should match 'PostgreSQL' via synonym resolution."""
        cand = _make_candidate(
            skills=["Postgres", "React.js", "K8s"],
            experience_years=5,
        )
        state = _build_state(
            [cand],
            requirements=["PostgreSQL", "React", "Kubernetes"],
        )
        result = asyncio.run(self.screener_node(state))
        scored = result.scored_candidates[0]
        # All 3 skills should match via synonyms
        assert scored.skills_match == 25.0, f"Expected 25.0, got {scored.skills_match}"
        assert len(scored.missing_skills) == 0

    def test_partial_skill_match(self):
        """Candidate missing some skills should have proportional score."""
        cand = _make_candidate(
            skills=["Python"],  # has 1 of 3
            experience_years=5,
        )
        state = _build_state(
            [cand],
            requirements=["Python", "Machine Learning", "SQL"],
        )
        result = asyncio.run(self.screener_node(state))
        scored = result.scored_candidates[0]
        expected_skill_score = round((1 / 3) * 25.0, 1)
        assert scored.skills_match == expected_skill_score

    def test_dynamic_experience_scoring_exact_match(self):
        """Candidate with exact target experience should get full marks."""
        cand = _make_candidate(experience_years=7)
        state = _build_state([cand], target_exp=7)
        result = asyncio.run(self.screener_node(state))
        scored = result.scored_candidates[0]
        assert scored.experience_match == 25.0

    def test_dynamic_experience_scoring_under_target(self):
        """Candidate with less experience than target should be penalized proportionally."""
        cand = _make_candidate(experience_years=3)
        state = _build_state([cand], target_exp=10)
        result = asyncio.run(self.screener_node(state))
        scored = result.scored_candidates[0]
        # distance = |3-10| / 10 = 0.7, score = max(0, 25 * (1-0.7)) = 7.5
        assert scored.experience_match == 7.5

    def test_dynamic_experience_scoring_over_target(self):
        """Candidate significantly over target should be penalized (overqualified)."""
        cand = _make_candidate(experience_years=15)
        state = _build_state([cand], target_exp=5)
        result = asyncio.run(self.screener_node(state))
        scored = result.scored_candidates[0]
        # distance = |15-5| / 5 = 2.0, score = max(0, 25*(1-2.0)) = 0.0
        assert scored.experience_match == 0.0

    def test_education_cs_field_bonus(self):
        """CS-related education should get higher score than unrelated fields."""
        cs_cand = _make_candidate(education="M.Tech in Computer Science, IIT Delhi")
        art_cand = _make_candidate(name="Art Major", education="B.A. in Fine Arts, JNU")
        no_edu = _make_candidate(name="No Edu", education="")

        state = _build_state([cs_cand, art_cand, no_edu])
        result = asyncio.run(self.screener_node(state))

        cs_scored = next(s for s in result.scored_candidates if s.candidate_id == cs_cand.id)
        art_scored = next(s for s in result.scored_candidates if s.candidate_id == art_cand.id)
        no_scored = next(s for s in result.scored_candidates if s.candidate_id == no_edu.id)

        assert cs_scored.education_match == 25.0
        assert art_scored.education_match == 15.0
        assert no_scored.education_match == 15.0  # empty edu gets base

    def test_cultural_fit_proximity_bonus(self):
        """Candidate within 30% of target experience should get cultural fit bonus."""
        # Target = 10, within 30% means 7-13 years
        close_cand = _make_candidate(name="Close", experience_years=9)
        far_cand = _make_candidate(name="Far", experience_years=2)

        state = _build_state([close_cand, far_cand], target_exp=10)
        result = asyncio.run(self.screener_node(state))

        close_scored = next(s for s in result.scored_candidates if s.candidate_id == close_cand.id)
        far_scored = next(s for s in result.scored_candidates if s.candidate_id == far_cand.id)

        assert close_scored.cultural_fit == 20.0  # 15 base + 5 bonus
        assert far_scored.cultural_fit == 15.0  # 15 base, no bonus

    def test_candidates_sorted_descending(self):
        """Scored candidates should be sorted by overall_score descending."""
        high = _make_candidate(name="High", skills=["Python", "Machine Learning", "SQL"], experience_years=5)
        low = _make_candidate(name="Low", skills=[], experience_years=1)

        state = _build_state([low, high])
        result = asyncio.run(self.screener_node(state))

        assert result.scored_candidates[0].candidate_name == "High"
        assert result.scored_candidates[1].candidate_name == "Low"

    def test_stage_transition(self):
        """Screener should advance stage to SHORTLIST_REVIEW."""
        cand = _make_candidate()
        state = _build_state([cand])
        result = asyncio.run(self.screener_node(state))
        assert result.current_stage == PipelineStage.SHORTLIST_REVIEW.value

    def test_empty_candidates_error(self):
        """Screener should set error when no candidates are provided."""
        state = _build_state([])
        result = asyncio.run(self.screener_node(state))
        assert result.error == "No candidates to screen"
