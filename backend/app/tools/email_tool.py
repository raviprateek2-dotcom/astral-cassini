"""Mock Email Tool for The Coordinator (Agent 5).

Simulates sending interview invitations via email.
In production, this would integrate with SendGrid / SMTP.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


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
    logger.info(f"[MOCK EMAIL] Sending interview invitation to {to_email}")
    logger.info(f"[MOCK EMAIL] Subject: Interview Invitation - {job_title}")

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

    logger.info(f"[MOCK EMAIL] Body preview: {email_body[:100]}...")

    return {
        "status": "sent",
        "to": to_email,
        "subject": f"Interview Invitation - {job_title}",
        "message_id": f"msg-{hash(to_email + interview_time) % 100000:05d}",
    }


def send_status_update(
    to_email: str,
    candidate_name: str,
    status: str,
    message: str,
) -> dict:
    """Send a mock status update email to a candidate."""
    logger.info(f"[MOCK EMAIL] Status update to {to_email}: {status}")

    return {
        "status": "sent",
        "to": to_email,
        "subject": f"Application Update: {status}",
        "message_id": f"msg-{hash(to_email + status) % 100000:05d}",
    }
