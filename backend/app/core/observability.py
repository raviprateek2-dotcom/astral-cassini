"""Lightweight in-memory observability counters.

This module is intentionally simple and dependency-free so it can be used from
API and WebSocket code paths without introducing new infrastructure.
"""

from __future__ import annotations

from threading import Lock

_lock = Lock()
_counters: dict[str, int] = {
    "ws_ticket_issued": 0,
    "ws_ticket_denied": 0,
    "ws_connect_success": 0,
    "ws_connect_rejected": 0,
    "agent_runs_success": 0,
    "agent_runs_failed": 0,
    "agent_duration_ms_sum": 0,
    "agent_duration_ms_count": 0,
}


def increment(name: str, value: int = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + value


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counters)


def record_agent_run(success: bool, duration_ms: float) -> None:
    with _lock:
        if success:
            _counters["agent_runs_success"] = _counters.get("agent_runs_success", 0) + 1
        else:
            _counters["agent_runs_failed"] = _counters.get("agent_runs_failed", 0) + 1
        _counters["agent_duration_ms_sum"] = _counters.get("agent_duration_ms_sum", 0) + int(duration_ms)
        _counters["agent_duration_ms_count"] = _counters.get("agent_duration_ms_count", 0) + 1
