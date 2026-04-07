"""Lightweight stability checks: concurrent API access and JSON error surface."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from starlette import status

from app.main import app

pytestmark = pytest.mark.stability


@pytest.mark.asyncio
async def test_health_concurrent_requests():
    """Many parallel GETs to /api/health should all succeed (SQLite + FAISS path)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        async def one() -> int:
            r = await client.get("/api/health")
            return r.status_code

        codes = await asyncio.gather(*[one() for _ in range(24)])
    assert all(c == status.HTTP_200_OK for c in codes)


@pytest.mark.asyncio
async def test_root_concurrent_requests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        async def one() -> int:
            r = await client.get("/")
            return r.status_code

        codes = await asyncio.gather(*[one() for _ in range(16)])
    assert all(c == status.HTTP_200_OK for c in codes)
