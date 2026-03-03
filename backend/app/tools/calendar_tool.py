"""Mock Calendar Tool for The Coordinator (Agent 5).

Simulates scheduling meetings via a calendar API.
In production, this would integrate with Google Calendar API.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def schedule_meeting(
    title: str,
    time: str,
    duration: int,
    attendees: list[str],
) -> dict:
    """Schedule a mock meeting.

    Args:
        title: Meeting title.
        time: ISO format datetime string.
        duration: Duration in minutes.
        attendees: List of attendee names/emails.

    Returns:
        Mock meeting confirmation.
    """
    logger.info(f"[MOCK CALENDAR] Scheduling: {title} at {time} for {duration}min")
    logger.info(f"[MOCK CALENDAR] Attendees: {', '.join(attendees)}")

    return {
        "status": "scheduled",
        "title": title,
        "time": time,
        "duration": duration,
        "attendees": attendees,
        "meeting_link": f"https://meet.example.com/{title.lower().replace(' ', '-')[:30]}",
        "calendar_event_id": f"evt-{hash(title) % 10000:04d}",
    }


def check_availability(
    attendees: list[str],
    date: str,
) -> dict:
    """Check mock availability for attendees on a given date.

    Returns:
        Mock availability slots.
    """
    return {
        "date": date,
        "available_slots": [
            {"start": f"{date}T09:00:00", "end": f"{date}T10:00:00"},
            {"start": f"{date}T10:30:00", "end": f"{date}T11:30:00"},
            {"start": f"{date}T14:00:00", "end": f"{date}T15:00:00"},
            {"start": f"{date}T15:30:00", "end": f"{date}T16:30:00"},
        ],
        "attendees": attendees,
    }
