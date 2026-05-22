"""Unit tests for offer template rendering and legal section validation.

Verifies that the offer letter template correctly fills all placeholders and
that the rendered output contains all required legal boilerplate sections.
"""

import pytest
from pathlib import Path


TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "app" / "agents" / "offer_template.md"

REQUIRED_LEGAL_SECTIONS = [
    "Background Verification",
    "Equal Opportunity",
    "At-Will Employment",
]

PLACEHOLDERS = [
    "{{candidate_name}}",
    "{{job_title}}",
    "{{department}}",
    "{{salary}}",
    "{{benefits_summary}}",
    "{{start_date}}",
    "{{personalized_impact_statement}}",
]


class TestOfferTemplate:
    """Tests for the offer letter Markdown template."""

    @pytest.fixture
    def template(self) -> str:
        assert TEMPLATE_PATH.exists(), f"Template not found at {TEMPLATE_PATH}"
        return TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_template_exists(self):
        assert TEMPLATE_PATH.exists()

    def test_all_placeholders_present(self, template: str):
        """Template should contain all expected placeholders."""
        for placeholder in PLACEHOLDERS:
            assert placeholder in template, f"Missing placeholder: {placeholder}"

    def test_all_legal_sections_present(self, template: str):
        """Template should contain all required legal boilerplate sections."""
        for section in REQUIRED_LEGAL_SECTIONS:
            assert section in template, f"Missing legal section: {section}"

    def test_placeholder_replacement(self, template: str):
        """All placeholders should be replaceable with real values."""
        replacements = {
            "{{candidate_name}}": "Priya Sharma",
            "{{job_title}}": "Senior ML Engineer",
            "{{department}}": "Engineering",
            "{{salary}}": "$150,000 - $180,000",
            "{{benefits_summary}}": "Medical, Dental, Vision, 401(k), 4 weeks PTO",
            "{{start_date}}": "July 1, 2026",
            "{{personalized_impact_statement}}": "You will lead our ML infrastructure team.",
        }
        rendered = template
        for placeholder, value in replacements.items():
            rendered = rendered.replace(placeholder, value)

        # No placeholders should remain
        assert "{{" not in rendered, "Unresolved placeholders remain after replacement"
        assert "}}" not in rendered, "Unresolved placeholders remain after replacement"

        # Actual values should be present
        for value in replacements.values():
            assert value in rendered

    def test_legal_sections_survive_replacement(self, template: str):
        """Legal sections should remain intact after placeholder replacement."""
        rendered = template.replace("{{candidate_name}}", "Test")
        rendered = rendered.replace("{{job_title}}", "Engineer")
        rendered = rendered.replace("{{department}}", "Eng")
        rendered = rendered.replace("{{salary}}", "$100k")
        rendered = rendered.replace("{{benefits_summary}}", "Standard")
        rendered = rendered.replace("{{start_date}}", "2026-07-01")
        rendered = rendered.replace("{{personalized_impact_statement}}", "Great impact.")

        for section in REQUIRED_LEGAL_SECTIONS:
            assert section in rendered, f"Legal section lost after replacement: {section}"

    def test_no_extra_undefined_placeholders(self, template: str):
        """Template should not contain any unknown {{ }} placeholders."""
        import re
        found = re.findall(r"\{\{(\w+)\}\}", template)
        expected_keys = {p.strip("{}") for p in PLACEHOLDERS}
        actual_keys = set(found)
        unexpected = actual_keys - expected_keys
        assert not unexpected, f"Unexpected placeholders: {unexpected}"
