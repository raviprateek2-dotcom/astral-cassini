"""Mock Calendar Tool for the Hiring Ops Coordinator (Agent 7).

Simulates scheduling meetings via a calendar API.
In production, this would integrate with Google Calendar API.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


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
    if settings.calendar_provider == "google":
        event = _schedule_google_meeting(title, time, duration, attendees)
        if event is not None:
            return event
        logger.warning("[CALENDAR] Falling back to mock provider after Google scheduling failure.")

    return _schedule_mock_meeting(title, time, duration, attendees)


def _schedule_mock_meeting(
    title: str,
    time: str,
    duration: int,
    attendees: list[str],
) -> dict:
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


def _schedule_google_meeting(
    title: str,
    time: str,
    duration: int,
    attendees: list[str],
) -> dict | None:
    if not settings.google_service_account_json:
        logger.warning("[GOOGLE CALENDAR] GOOGLE_SERVICE_ACCOUNT_JSON is not set.")
        return None
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except Exception as exc:
        logger.warning("[GOOGLE CALENDAR] Missing Google client dependencies: %s", exc)
        return None

    try:
        start_dt = datetime.fromisoformat(time.replace("Z", "+00:00"))
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(minutes=duration)

        credentials = service_account.Credentials.from_service_account_file(
            settings.google_service_account_json,
            scopes=GOOGLE_CALENDAR_SCOPES,
        )
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

        body = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat()},
            "end": {"dateTime": end_dt.isoformat()},
            "attendees": [{"email": email} for email in attendees],
            "conferenceData": {
                "createRequest": {
                    "requestId": f"prohr-{abs(hash((title, time))) % 10_000_000}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }
        event = (
            service.events()
            .insert(
                calendarId=settings.google_calendar_id,
                body=body,
                conferenceDataVersion=1,
                sendUpdates="all",
            )
            .execute()
        )
        meeting_link = event.get("hangoutLink") or event.get("htmlLink") or ""
        logger.info("[GOOGLE CALENDAR] Created event %s", event.get("id"))
        return {
            "status": "scheduled",
            "title": title,
            "time": start_dt.isoformat(),
            "duration": duration,
            "attendees": attendees,
            "meeting_link": meeting_link,
            "calendar_event_id": event.get("id", ""),
        }
    except Exception as exc:
        logger.warning("[GOOGLE CALENDAR] Failed to create event: %s", exc)
        return None


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
