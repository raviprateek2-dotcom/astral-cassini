"""FastAPI application entry point for PRO HR."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import jobs, candidates, workflow, websocket, auth, analytics
from app.core.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
import os

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
    
    # Auto-create demo users if they don't exist
    from app.core.database import SessionLocal
    from app.models.db_models import User
    from app.core.auth import hash_password
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@prohr.ai").first():
            db.add(User(
                email="admin@prohr.ai",
                full_name="System Admin",
                hashed_password=hash_password("admin123"),
                role="admin"
            ))
        if not db.query(User).filter(User.email == "hr@prohr.ai").first():
            db.add(User(
                email="hr@prohr.ai",
                full_name="HR Manager",
                hashed_password=hash_password("hr123"),
                role="hr_manager",
                department="Engineering"
            ))
        db.commit()
    finally:
        db.close()
        
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
