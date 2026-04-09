"""initial schema

Revision ID: 20260409_0001
Revises:
Create Date: 2026-04-09 20:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260409_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=20), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column("requirements", sa.JSON(), nullable=True),
        sa.Column("preferred_qualifications", sa.JSON(), nullable=True),
        sa.Column("current_stage", sa.String(length=50), nullable=True),
        sa.Column("jd_approval", sa.String(length=20), nullable=True),
        sa.Column("shortlist_approval", sa.String(length=20), nullable=True),
        sa.Column("hire_approval", sa.String(length=20), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("outreach_completed", sa.Boolean(), nullable=True),
        sa.Column("offer_sent", sa.Boolean(), nullable=True),
        sa.Column("avg_match_percentage", sa.Float(), nullable=True),
        sa.Column("workflow_state", sa.JSON(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index(op.f("ix_jobs_id"), "jobs", ["id"], unique=False)
    op.create_index(op.f("ix_jobs_job_id"), "jobs", ["job_id"], unique=True)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=20), nullable=False),
        sa.Column("agent", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("stage", sa.String(length=50), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_id"), "audit_events", ["id"], unique=False)
    op.create_index(op.f("ix_audit_events_timestamp"), "audit_events", ["timestamp"], unique=False)

    op.create_table(
        "candidate_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=20), nullable=False),
        sa.Column("candidate_id", sa.String(length=50), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("match_percentage", sa.Float(), nullable=True),
        sa.Column("skills_match", sa.Float(), nullable=True),
        sa.Column("experience_match", sa.Float(), nullable=True),
        sa.Column("education_match", sa.Float(), nullable=True),
        sa.Column("cultural_fit", sa.Float(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("gaps", sa.JSON(), nullable=True),
        sa.Column("missing_skills", sa.JSON(), nullable=True),
        sa.Column("overqualification", sa.JSON(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_candidate_scores_id"), "candidate_scores", ["id"], unique=False)

    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=20), nullable=False),
        sa.Column("candidate_id", sa.String(length=50), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("interview_type", sa.String(length=50), nullable=True),
        sa.Column("scheduled_time", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("interviewers", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("technical_score", sa.Float(), nullable=True),
        sa.Column("communication_score", sa.Float(), nullable=True),
        sa.Column("problem_solving_score", sa.Float(), nullable=True),
        sa.Column("cultural_fit_score", sa.Float(), nullable=True),
        sa.Column("key_observations", sa.JSON(), nullable=True),
        sa.Column("concerns", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interviews_id"), "interviews", ["id"], unique=False)

    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=20), nullable=False),
        sa.Column("candidate_id", sa.String(length=50), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("offer_markdown", sa.Text(), nullable=True),
        sa.Column("salary_offered", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("valid_until", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_offers_id"), "offers", ["id"], unique=False)

    op.create_table(
        "outreach",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=20), nullable=False),
        sa.Column("candidate_id", sa.String(length=50), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("email_subject", sa.String(length=255), nullable=True),
        sa.Column("email_body", sa.Text(), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("engagement_level", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outreach_id"), "outreach", ["id"], unique=False)

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=20), nullable=False),
        sa.Column("candidate_id", sa.String(length=50), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("overall_weighted_score", sa.Float(), nullable=True),
        sa.Column("screening_weight", sa.Float(), nullable=True),
        sa.Column("interview_weight", sa.Float(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("risk_factors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendations_id"), "recommendations", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendations_id"), table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index(op.f("ix_outreach_id"), table_name="outreach")
    op.drop_table("outreach")
    op.drop_index(op.f("ix_offers_id"), table_name="offers")
    op.drop_table("offers")
    op.drop_index(op.f("ix_interviews_id"), table_name="interviews")
    op.drop_table("interviews")
    op.drop_index(op.f("ix_candidate_scores_id"), table_name="candidate_scores")
    op.drop_table("candidate_scores")
    op.drop_index(op.f("ix_audit_events_timestamp"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_id"), table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index(op.f("ix_jobs_job_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
