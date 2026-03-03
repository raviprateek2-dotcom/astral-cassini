"""Candidates API routes."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.graph.workflow import get_workflow_status
from app.rag.parser import parse_resume_pdf, parse_resume_text
from app.rag.embeddings import index_resume, get_collection_count

router = APIRouter(prefix="/api", tags=["Candidates"])

UPLOAD_DIR = Path("data/uploads")


@router.get("/jobs/{job_id}/candidates")
async def get_candidates(job_id: str):
    """Get matched candidates for a job."""
    status = get_workflow_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    state = status.get("state", {})
    return {
        "job_id": job_id,
        "candidates": state.get("candidates", []),
        "scored_candidates": state.get("scored_candidates", []),
    }


@router.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume PDF and index it in the vector store."""
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
async def resume_count():
    """Get the number of indexed resumes."""
    return {"count": get_collection_count()}
