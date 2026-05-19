"""SQLAlchemy database engine, session, and base model."""

from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from alembic import command
from alembic.config import Config

def _normalize_database_url(database_url: str) -> str:
    """Normalize sqlite URLs to absolute paths for stable cwd-independent behavior."""
    if not database_url.startswith("sqlite:///"):
        return database_url
    sqlite_path = database_url.replace("sqlite:///", "", 1)
    if sqlite_path == ":memory:":
        return database_url
    path = Path(sqlite_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return f"sqlite:///{path.as_posix()}"


# Default to SQLite for local dev; set DATABASE_URL env var for PostgreSQL
RAW_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/prohr.db")
DATABASE_URL = _normalize_database_url(RAW_DATABASE_URL)

# SQLite needs check_same_thread=False for FastAPI threading
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    """Create parent directory for local sqlite files when needed."""
    normalized = _normalize_database_url(database_url)
    if not normalized.startswith("sqlite:///"):
        return
    sqlite_path = normalized.replace("sqlite:///", "", 1)
    if sqlite_path == ":memory:":
        return
    path = Path(sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database. Skips Alembic upgrade when schema is already at head."""
    import logging as _logmod
    _logger = _logmod.getLogger(__name__)

    _ensure_sqlite_parent_dir(DATABASE_URL)
    backend_root = Path(__file__).resolve().parents[2]

    # Create any missing tables (fast, no exclusive lock needed)
    Base.metadata.create_all(bind=engine, checkfirst=True)

    alembic_ini = backend_root / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

    # Only run Alembic upgrade if we are behind head revision
    try:
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            current_rev = ctx.get_current_revision()
        head_rev = ScriptDirectory.from_config(config).get_current_head()
        if current_rev == head_rev:
            _logger.info("DB schema already at head revision %s", head_rev)
            return
        _logger.info("Running Alembic upgrade from %s to %s", current_rev, head_rev)
        command.upgrade(config, "head")
    except Exception as exc:
        _logger.warning("Alembic revision check/upgrade skipped: %s", exc)
        if _can_stamp_existing_schema():
            try:
                command.stamp(config, "head")
            except Exception:
                pass



def _can_stamp_existing_schema() -> bool:
    """Allow one-time stamp when tables predate Alembic versioning."""
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        return "alembic_version" not in tables and bool(tables)
    except Exception:
        return False
