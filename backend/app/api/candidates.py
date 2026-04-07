"""Candidates API routes."""

from __future__ import annotations

import uuid
from pathlib import Path

from typing import Annotated
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import RequireHR
from app.core.orchestrator import get_workflow_status
from app.models.db_models import User
from app.rag.parser import parse_resume_pdf, parse_resume_text
from app.rag.embeddings import index_resume, get_collection_count

router = APIRouter(prefix="/api", tags=["Candidates"])

UPLOAD_DIR = Path("data/uploads")


@router.get("/jobs/{job_id}/candidates")
async def get_candidates(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, RequireHR],
):
    """Get matched candidates for a job."""
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    state = status.get("state", {})
    return {
        "job_id": job_id,
        "candidates": state.get("candidates", []),
        "scored_candidates": state.get("scored_candidates", []),
    }


@router.post("/resumes/upload", deprecated=True)
async def upload_resume(
    response: Response,
    _: Annotated[User, RequireHR],
    file: UploadFile = File(...),
):
    """Index a resume without a job id (utility / admin-style upload).

    Accepts **PDF** (parsed with ``parse_resume_pdf``) or other files as **UTF-8 text**
    (``parse_resume_text``). Does **not** enforce pipeline stage.

    **Preferred:** ``POST /api/jobs/{job_id}/resumes`` (product UI uses that route).

    **Deprecation:** Marked deprecated in OpenAPI; responses may include ``Deprecation``,
    ``Sunset`` (RFC 8594), and ``Link`` for the job-scoped replacement. See CHANGELOG.
    """
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 07 Apr 2027 00:00:00 GMT"
    response.headers["Link"] = '</api/jobs/>; rel="related"; title="POST /api/jobs/{job_id}/resumes"'
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Save the uploaded file
    file_id = str(uuid.uuid4())[:8]
    file_ext = Path(file.filename or "resume.pdf").suffix
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse and index
    if file_ext.lower() == ".pdf":
        parsed = parse_resume_pdf(str(file_path))
    else:
        text_content = content.decode("utf-8", errors="ignore")
        parsed = parse_resume_text(text_content)

    parsed["id"] = file_id
    doc_id = index_resume(parsed)

    return {
        "file_id": file_id,
        "doc_id": doc_id,
        "name": parsed.get("name", "Unknown"),
        "skills": parsed.get("skills", []),
        "indexed": True,
        "collection_size": get_collection_count(),
    }


@router.get("/resumes/count")
async def resume_count(_: Annotated[User, RequireHR]):
    """Get the number of indexed resumes."""
    return {"count": get_collection_count()}
