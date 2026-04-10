"""SQLAlchemy ORM models for the entire platform.

Tables:
- users        — platform users with roles
- jobs         — recruitment pipelines
- candidate_scores — screener output per candidate per job
- interviews   — scheduled interviews
- audit_events — complete immutable event log
- recommendations — final decider output
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean,
    DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer", nullable=False)
    # roles: admin | hr_manager | business_lead | viewer
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    last_login = Column(DateTime, nullable=True)

    jobs = relationship("Job", back_populates="created_by")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(20), unique=True, index=True, nullable=False)
    job_title = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    location = Column(String(100), default="Remote")
    salary_range = Column(String(100))
    requirements = Column(JSON, default=list)
    preferred_qualifications = Column(JSON, default=list)

    # Workflow state
    current_stage = Column(String(50), default="intake")
    jd_approval = Column(String(20), default="pending")
    shortlist_approval = Column(String(20), default="pending")
    hire_approval = Column(String(20), default="pending")
    job_description = Column(Text, default="")
    
    # Analytics / Aggregate status
    outreach_completed = Column(Boolean, default=False)
    offer_sent = Column(Boolean, default=False)
    avg_match_percentage = Column(Float, default=0.0)

    # Full LangGraph state (JSON blob for restore)
    workflow_state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", back_populates="jobs")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    scores = relationship("CandidateScore", back_populates="job", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="job", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="job", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="job", cascade="all, delete-orphan")
    outreach = relationship("Outreach", back_populates="job", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="job", cascade="all, delete-orphan")


class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(20), ForeignKey("jobs.job_id"), nullable=False)
    candidate_id = Column(String(50), nullable=False)
    candidate_name = Column(String(255), nullable=False)

    overall_score = Column(Float, default=0.0)
    match_percentage = Column(Float, default=0.0)
    skills_match = Column(Float, default=0.0)
    experience_match = Column(Float, default=0.0)
    education_match = Column(Float, default=0.0)
    cultural_fit = Column(Float, default=0.0)

    strengths = Column(JSON, default=list)
    gaps = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    overqualification = Column(JSON, default=list)
    reasoning = Column(Text, default="")

    created_at = Column(DateTime, default=utc_now)
    job = relationship("Job", back_populates="scores")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(20), ForeignKey("jobs.job_id"), nullable=False)
    candidate_id = Column(String(50), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    interview_type = Column(String(50), default="technical")
    scheduled_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=60)
    interviewers = Column(JSON, default=list)
    status = Column(String(50), default="scheduled")

    # Assessment fields
    overall_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    problem_solving_score = Column(Float, nullable=True)
    cultural_fit_score = Column(Float, nullable=True)
    key_observations = Column(JSON, default=list)
    concerns = Column(JSON, default=list)

    created_at = Column(DateTime, default=utc_now)
    job = relationship("Job", back_populates="interviews")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(20), ForeignKey("jobs.job_id"), nullable=False)
    agent = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text, default="")
    stage = Column(String(50), default="")
    timestamp = Column(DateTime, default=utc_now, index=True)

    job = relationship("Job", back_populates="audit_events")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(20), ForeignKey("jobs.job_id"), nullable=False)
    candidate_id = Column(String(50), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    decision = Column(String(20), nullable=False)   # hire | no_hire | maybe
    confidence = Column(Float, default=0.0)
    overall_weighted_score = Column(Float, default=0.0)
    screening_weight = Column(Float, default=0.0)
    interview_weight = Column(Float, default=0.0)
    reasoning = Column(Text, default="")
    risk_factors = Column(JSON, default=list)

    created_at = Column(DateTime, default=utc_now)
    job = relationship("Job", back_populates="recommendations")


class Outreach(Base):
    __tablename__ = "outreach"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(20), ForeignKey("jobs.job_id"), nullable=False)
    candidate_id = Column(String(50), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    email_subject = Column(String(255))
    email_body = Column(Text)
    response_text = Column(Text, nullable=True)
    engagement_level = Column(String(50), default="High")  # High | Medium | Low
    status = Column(String(50), default="sent")  # sent | responding | scheduled
    sent_at = Column(DateTime, default=utc_now)

    job = relationship("Job", back_populates="outreach")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(20), ForeignKey("jobs.job_id"), nullable=False)
    candidate_id = Column(String(50), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    offer_markdown = Column(Text)
    salary_offered = Column(String(100))
    status = Column(String(50), default="draft")  # draft | sent | accepted | rejected
    valid_until = Column(String(100))
    created_at = Column(DateTime, default=utc_now)

    job = relationship("Job", back_populates="offers")
