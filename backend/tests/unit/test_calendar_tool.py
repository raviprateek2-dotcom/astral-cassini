import pytest

pytestmark = pytest.mark.unit

from app.tools import calendar_tool


def test_schedule_meeting_uses_mock_by_default():
    result = calendar_tool.schedule_meeting(
        title="Interview: Alice",
        time="2026-04-09T10:00:00",
        duration=60,
        attendees=["alice@example.com"],
    )
    assert result["status"] == "scheduled"
    assert result["meeting_link"].startswith("https://meet.example.com/")
    assert result["calendar_event_id"].startswith("evt-")


def test_schedule_meeting_falls_back_when_google_unconfigured(monkeypatch):
    monkeypatch.setattr(calendar_tool.settings, "calendar_provider", "google")
    monkeypatch.setattr(calendar_tool.settings, "google_service_account_json", "")
    result = calendar_tool.schedule_meeting(
        title="Interview: Bob",
        time="2026-04-10T11:00:00",
        duration=45,
        attendees=["bob@example.com"],
    )
    assert result["meeting_link"].startswith("https://meet.example.com/")
