"""Mock Email Tool for The Coordinator (Agent 5).

Simulates sending interview invitations via email.
In production, this would integrate with SendGrid / SMTP.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def _send_via_smtp(to_email: str, subject: str, body: str) -> dict:
    msg = EmailMessage()
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
    return {
        "status": "sent",
        "to": to_email,
        "subject": subject,
        "provider": "smtp",
        "message_id": f"smtp-{hash(to_email + subject) % 100000:05d}",
    }


def send_interview_invitation(
    to_email: str,
    candidate_name: str,
    job_title: str,
    interview_time: str,
    meeting_link: str,
) -> dict:
    """Send a mock interview invitation email.

    Args:
        to_email: Candidate's email address.
        candidate_name: Candidate's full name.
        job_title: Position being interviewed for.
        interview_time: ISO format datetime string.
        meeting_link: Video meeting URL.

    Returns:
        Mock email delivery confirmation.
    """
    email_body = f"""
Dear {candidate_name},

We are pleased to invite you for an interview for the position of {job_title}.

Interview Details:
- Date & Time: {interview_time}
- Format: Video Call
- Meeting Link: {meeting_link}

Please confirm your attendance by replying to this email.

Best regards,
HR Team — PRO HR
"""
    subject = f"Interview Invitation - {job_title}"
    if settings.email_provider == "smtp" and settings.smtp_host:
        try:
            return _send_via_smtp(to_email, subject, email_body)
        except Exception:
            logger.exception("SMTP send failed, falling back to mock delivery.")

    logger.info(f"[MOCK EMAIL] Sending interview invitation to {to_email}")
    logger.info(f"[MOCK EMAIL] Subject: {subject}")
    logger.info(f"[MOCK EMAIL] Body preview: {email_body[:100]}...")

    return {
        "status": "sent",
        "to": to_email,
        "subject": subject,
        "provider": "mock",
        "message_id": f"msg-{hash(to_email + interview_time) % 100000:05d}",
    }


def send_status_update(
    to_email: str,
    candidate_name: str,
    status: str,
    message: str,
) -> dict:
    """Send a mock status update email to a candidate."""
    subject = f"Application Update: {status}"
    if settings.email_provider == "smtp" and settings.smtp_host:
        try:
            return _send_via_smtp(to_email, subject, message)
        except Exception:
            logger.exception("SMTP status update failed, falling back to mock delivery.")
    logger.info(f"[MOCK EMAIL] Status update to {to_email}: {status}")

    return {
        "status": "sent",
        "to": to_email,
        "subject": subject,
        "provider": "mock",
        "message_id": f"msg-{hash(to_email + status) % 100000:05d}",
    }
