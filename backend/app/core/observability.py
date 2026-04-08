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
}


def increment(name: str, value: int = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + value


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counters)
