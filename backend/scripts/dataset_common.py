from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

csv.field_size_limit(10_000_000)


TABLE_SPECS = {
    "users": {
        "columns": [
            "email",
            "full_name",
            "hashed_password",
            "role",
            "department",
            "is_active",
            "created_at",
            "last_login",
        ],
        "upsert_keys": ["email"],
    },
    "jobs": {
        "columns": [
            "job_id",
            "job_title",
            "department",
            "location",
            "salary_range",
            "requirements",
            "preferred_qualifications",
            "current_stage",
            "jd_approval",
            "shortlist_approval",
            "hire_approval",
            "job_description",
            "outreach_completed",
            "offer_sent",
            "avg_match_percentage",
            "workflow_state",
            "created_by_id",
            "created_at",
            "updated_at",
            "completed_at",
        ],
        "upsert_keys": ["job_id"],
    },
    "candidate_scores": {
        "columns": [
            "job_id",
            "candidate_id",
            "candidate_name",
            "overall_score",
            "match_percentage",
            "skills_match",
            "experience_match",
            "education_match",
            "cultural_fit",
            "strengths",
            "gaps",
            "missing_skills",
            "overqualification",
            "reasoning",
            "created_at",
        ],
        "upsert_keys": ["job_id", "candidate_id"],
    },
    "interviews": {
        "columns": [
            "job_id",
            "candidate_id",
            "candidate_name",
            "interview_type",
            "scheduled_time",
            "duration_minutes",
            "interviewers",
            "status",
            "overall_score",
            "technical_score",
            "communication_score",
            "problem_solving_score",
            "cultural_fit_score",
            "key_observations",
            "concerns",
            "created_at",
        ],
        "upsert_keys": ["job_id", "candidate_id", "scheduled_time"],
    },
    "recommendations": {
        "columns": [
            "job_id",
            "candidate_id",
            "candidate_name",
            "decision",
            "confidence",
            "overall_weighted_score",
            "screening_weight",
            "interview_weight",
            "reasoning",
            "risk_factors",
            "created_at",
        ],
        "upsert_keys": ["job_id", "candidate_id"],
    },
    "audit_events": {
        "columns": ["job_id", "agent", "action", "details", "stage", "timestamp"],
        "upsert_keys": ["job_id", "timestamp", "action"],
    },
    "outreach": {
        "columns": [
            "job_id",
            "candidate_id",
            "candidate_name",
            "email_subject",
            "email_body",
            "response_text",
            "engagement_level",
            "status",
            "sent_at",
        ],
        "upsert_keys": ["job_id", "candidate_id"],
    },
    "offers": {
        "columns": [
            "job_id",
            "candidate_id",
            "candidate_name",
            "offer_markdown",
            "salary_offered",
            "status",
            "valid_until",
            "created_at",
        ],
        "upsert_keys": ["job_id", "candidate_id"],
    },
}

JSON_COLUMNS = {
    "jobs": {"requirements", "preferred_qualifications", "workflow_state"},
    "candidate_scores": {"strengths", "gaps", "missing_skills", "overqualification"},
    "interviews": {"interviewers", "key_observations", "concerns"},
    "recommendations": {"risk_factors"},
}

BOOL_COLUMNS = {
    "users": {"is_active"},
    "jobs": {"outreach_completed", "offer_sent"},
}

INT_COLUMNS = {
    "jobs": {"created_by_id"},
    "interviews": {"duration_minutes"},
}

FLOAT_COLUMNS = {
    "jobs": {"avg_match_percentage"},
    "candidate_scores": {
        "overall_score",
        "match_percentage",
        "skills_match",
        "experience_match",
        "education_match",
        "cultural_fit",
    },
    "interviews": {
        "overall_score",
        "technical_score",
        "communication_score",
        "problem_solving_score",
        "cultural_fit_score",
    },
    "recommendations": {
        "confidence",
        "overall_weighted_score",
        "screening_weight",
        "interview_weight",
    },
}

DATETIME_COLUMNS = {
    "users": {"created_at", "last_login"},
    "jobs": {"created_at", "updated_at", "completed_at"},
    "candidate_scores": {"created_at"},
    "interviews": {"created_at", "scheduled_time"},
    "recommendations": {"created_at"},
    "audit_events": {"timestamp"},
    "outreach": {"sent_at"},
    "offers": {"created_at"},
}

ALLOWED_JOB_STAGES = {
    "intake",
    "jd_drafting",
    "jd_review",
    "sourcing",
    "screening",
    "shortlist_review",
    "outreach",
    "engagement",
    "scheduling",
    "interviewing",
    "decision",
    "hire_review",
    "offer",
    "completed",
}

ALLOWED_DECISIONS = {"hire", "no_hire", "maybe"}


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    rows_by_table: dict[str, int]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def serialize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def parse_bool(value: str) -> bool | None:
    if value == "":
        return None
    v = value.strip().lower()
    if v in {"true", "1", "yes"}:
        return True
    if v in {"false", "0", "no"}:
        return False
    raise ValueError(f"Invalid boolean: {value}")


def parse_datetime(value: str) -> datetime | None:
    if value == "":
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_json(value: str) -> Any:
    if value == "":
        return None
    return json.loads(value)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

