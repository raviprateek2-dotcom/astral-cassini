import os
import tempfile
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

import app.core.orchestrator as orch_mod

# Patch before importing app routers so call sites resolve mocked ``await start_orchestration``.
_orch_start_patcher = patch.object(
    orch_mod,
    "start_orchestration",
    AsyncMock(return_value=True),
)
_orch_start_patcher.start()
orch_mod._orch_start_patcher_for_tests = _orch_start_patcher


def _load_app_after_orch_patch() -> None:
    """Bind ``app`` and related symbols only after the orchestration mock is active.

    Module-level ``from app…`` after executable code triggers Ruff E402; imports inside
    this function do not.
    """
    global app, database, Base, get_db, SharedState, settings
    from app.config import settings as _settings
    from app.core import database as _database
    from app.core.database import Base as _Base, get_db as _get_db
    from app.main import app as _app
    from app.models.state import SharedState as _SharedState

    app = _app
    database = _database
    Base = _Base
    get_db = _get_db
    SharedState = _SharedState
    settings = _settings


_load_app_after_orch_patch()

# Test Database Setup — temporary file DB for isolation and multi-connection support
_db_fd, db_path = tempfile.mkstemp()
os.close(_db_fd)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Monkeypatch the database module's SessionLocal so background tasks use our test DB
database.SessionLocal = TestingSessionLocal
database.engine = engine


@pytest.fixture(scope="session", autouse=True)
def db_setup():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_state() -> SharedState:
    return SharedState(
        job_id="test-job-123",
        job_title="Senior AI Engineer",
        department="Engineering",
        requirements=["Python", "PyTorch", "Testing"],
        location="Remote",
    )


@pytest.fixture
def mock_llm_response():
    """Mock the LLM's structured output."""
    return {
        "jd": "<thought_process>Strategically aligning with role.</thought_process><job_description># Senior AI Engineer\n\nYou will build robots.</job_description><bias_audit>Clear of gender bias.</bias_audit>",
        "screening": {
            "overall_score": 85.0,
            "skills_match": 22.0,
            "experience_match": 21.0,
            "education_match": 20.0,
            "cultural_fit": 22.0,
            "reasoning": "Strong match for PyTorch requirements.",
        },
    }


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Ensure tests don't hit real APIs by default."""
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "langchain_api_key", "")
