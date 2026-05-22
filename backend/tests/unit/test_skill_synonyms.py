"""Unit tests for the skill synonym dictionary and matching utilities.

Validates ``normalize_skill()``, ``skills_match()``, and the synonym
dictionary coverage for common technology aliases.
"""

import pytest

from app.agents.skill_synonyms import (
    SKILL_SYNONYMS,
    normalize_skill,
    skills_match,
    _ALIAS_TO_CANONICAL,
)


# ---------------------------------------------------------------------------
# normalize_skill()
# ---------------------------------------------------------------------------


class TestNormalizeSkill:
    """Tests for canonical skill name resolution."""

    @pytest.mark.parametrize(
        "input_skill, expected_canonical",
        [
            ("PostgreSQL", "postgresql"),
            ("Postgres", "postgresql"),
            ("PSQL", "postgresql"),
            ("React.js", "react"),
            ("ReactJS", "react"),
            ("React", "react"),
            ("Node.js", "node.js"),
            ("Node", "node.js"),
            ("NodeJS", "node.js"),
            ("K8s", "kubernetes"),
            ("Kubernetes", "kubernetes"),
            ("Docker", "docker"),
            ("Dockerfile", "docker"),
            ("gpt-4o", "gpt-4o"),  # Unknown skill — returns lowered
            ("ML", "machine learning"),
            ("NLP", "natural language processing"),
            ("AWS", "aws"),
            ("Amazon Web Services", "aws"),
            ("TypeScript", "typescript"),
            ("TS", "typescript"),
            ("JS", "javascript"),
            ("ECMAScript", "javascript"),
        ],
    )
    def test_known_aliases(self, input_skill: str, expected_canonical: str):
        assert normalize_skill(input_skill) == expected_canonical

    def test_unknown_skill_lowered(self):
        assert normalize_skill("Underwater Welding") == "underwater welding"

    def test_whitespace_handling(self):
        assert normalize_skill("  React.js  ") == "react"

    def test_empty_string(self):
        assert normalize_skill("") == ""


# ---------------------------------------------------------------------------
# skills_match()
# ---------------------------------------------------------------------------


class TestSkillsMatch:
    """Tests for the bidirectional skill matching function."""

    @pytest.mark.parametrize(
        "required, candidate, should_match",
        [
            # Direct canonical matches
            ("PostgreSQL", "Postgres", True),
            ("React", "React.js", True),
            ("Kubernetes", "K8s", True),
            ("Python", "Python", True),
            ("TypeScript", "TS", True),
            ("Machine Learning", "ML", True),
            ("Node.js", "NodeJS", True),
            # Substring containment fallback
            ("GraphQL", "GraphQL APIs", True),
            ("SQL", "PostgreSQL", True),
            ("Docker", "Docker Compose", True),
            # Non-matches
            ("Python", "Java", False),
            ("React", "Angular", False),
            ("PostgreSQL", "MongoDB", False),
            ("Kubernetes", "Terraform", False),
            ("FastAPI", "Django", False),
        ],
    )
    def test_matching_pairs(self, required: str, candidate: str, should_match: bool):
        assert skills_match(required, candidate) == should_match

    def test_case_insensitive(self):
        assert skills_match("PYTHON", "python") is True
        assert skills_match("react", "REACT.JS") is True

    def test_whitespace_tolerance(self):
        assert skills_match("  Docker  ", "docker") is True


# ---------------------------------------------------------------------------
# Synonym dictionary integrity
# ---------------------------------------------------------------------------


class TestSynonymDictionary:
    """Structural tests for the synonym dictionary."""

    def test_no_overlapping_aliases(self):
        """Every alias must map to exactly one canonical name."""
        seen: dict[str, str] = {}
        for canonical, aliases in SKILL_SYNONYMS.items():
            for alias in aliases:
                if alias in seen:
                    pytest.fail(
                        f"Alias '{alias}' maps to both "
                        f"'{seen[alias]}' and '{canonical}'"
                    )
                seen[alias] = canonical

    def test_canonical_not_in_own_aliases(self):
        """A canonical name should not be listed in its own alias set."""
        for canonical, aliases in SKILL_SYNONYMS.items():
            assert canonical not in aliases, (
                f"Canonical '{canonical}' is also listed as its own alias"
            )

    def test_reverse_map_populated(self):
        """The reverse map should contain entries for every canonical + alias."""
        total_expected = sum(
            1 + len(aliases) for aliases in SKILL_SYNONYMS.values()
        )
        assert len(_ALIAS_TO_CANONICAL) == total_expected

    def test_minimum_coverage(self):
        """The dictionary should cover at least 30 canonical skills."""
        assert len(SKILL_SYNONYMS) >= 30
