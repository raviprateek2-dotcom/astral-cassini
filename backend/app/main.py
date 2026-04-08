"""FastAPI application entry point for PRO HR."""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import jobs, candidates, workflow, websocket, auth, analytics
from app.core.database import init_db
from app.core.observability import snapshot as observability_snapshot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)


def _cors_allow_origins() -> list[str]:
    """Build a deduplicated list: configured frontend, localhost dev, optional extra origins."""
    defaults = [
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    extras = [
        o.strip()
        for o in settings.cors_extra_origins.split(",")
        if o.strip()
    ]
    seen: set[str] = set()
    out: list[str] = []
    for origin in defaults + extras:
        if origin not in seen:
            seen.add(origin)
            out.append(origin)
    return out


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set LangSmith environment variables before graph execution
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        if settings.langchain_endpoint:
            os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
        logger.info(f"LangSmith Tracing configured for project: {settings.langchain_project}")

    # Initialize SQLAlchemy database tables on startup
    init_db()
    
    # Auto-create demo users only when explicitly enabled in development.
    seed_demo_users = os.getenv("SEED_DEMO_USERS", "false").lower() == "true"
    is_dev = settings.app_env.lower() in {"development", "dev", "local"}
    if seed_demo_users and is_dev:
        from app.core.database import SessionLocal
        from app.models.db_models import User
        from app.core.auth import hash_password
        demo_admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "")
        demo_hr_password = os.getenv("DEMO_HR_PASSWORD", "")
        if len(demo_admin_password) < 8 or len(demo_hr_password) < 8:
            raise RuntimeError(
                "SEED_DEMO_USERS=true requires DEMO_ADMIN_PASSWORD and DEMO_HR_PASSWORD (8+ chars)."
            )

        db = SessionLocal()
        try:
            if not db.query(User).filter(User.email == "admin@prohr.ai").first():
                db.add(User(
                    email="admin@prohr.ai",
                    full_name="System Admin",
                    hashed_password=hash_password(demo_admin_password),
                    role="admin"
                ))
            if not db.query(User).filter(User.email == "hr@prohr.ai").first():
                db.add(User(
                    email="hr@prohr.ai",
                    full_name="HR Manager",
                    hashed_password=hash_password(demo_hr_password),
                    role="hr_manager",
                    department="Engineering"
                ))
            db.commit()
        finally:
            db.close()

    google_calendar_ready = bool(settings.google_service_account_json)
    logger.info(
        "Calendar provider configured: provider=%s google_credentials_path_set=%s calendar_id=%s",
        settings.calendar_provider,
        google_calendar_ready,
        settings.google_calendar_id if settings.calendar_provider == "google" else "n/a",
    )
        
    yield

# Create the FastAPI app
app = FastAPI(
    title="PRO HR",
    description="PRO HR Autonomous Multi-Agent Recruitment Ecosystem",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware (set FRONTEND_URL + optional CORS_EXTRA_ORIGINS in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def stable_api_errors(request: Request, call_next):
    """Turn unhandled exceptions into JSON 500s; preserve FastAPI HTTP and validation errors."""
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request completed id=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
    except HTTPException:
        raise
    except RequestValidationError:
        raise
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "Unhandled exception id=%s method=%s path=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        return JSONResponse(
            status_code=500,
            headers={"x-request-id": request_id},
            content={"detail": "Internal server error", "request_id": request_id},
        )


# Include routers
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(workflow.router)
app.include_router(websocket.router)



@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "PRO HR",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    """Detailed health check."""
    from app.rag.embeddings import get_collection_count
    return {
        "status": "healthy",
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "indexed_resumes": get_collection_count(),
        "openai_configured": bool(settings.openai_api_key),
        "observability": observability_snapshot(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
