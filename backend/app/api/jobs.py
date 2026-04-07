"""Jobs API routes."""

from __future__ import annotations

import os
import uuid
import tempfile
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, RequireHR
from app.models.db_models import User
from app.core.orchestrator import (
    start_workflow,
    get_workflow_status,
    get_all_workflows,
    resume_workflow,
)
from app.rag.parser import parse_resume_pdf
from app.rag.embeddings import index_resume

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


class CreateJobRequest(BaseModel):
    """Request body for creating a new job requisition."""
    job_title: str
    department: str
    requirements: list[str]
    preferred_qualifications: list[str] = []
    location: str = "Remote"
    salary_range: str = "Competitive"


class JobResponse(BaseModel):
    """Response for job operations."""
    job_id: str
    status: str
    current_stage: str
    state: dict = {}
    error: str = ""


@router.post("", response_model=JobResponse)
async def create_job(
    req: CreateJobRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireHR],
):
    """Create a new job requisition and start the recruitment workflow.
    Requires HR Manager or Admin role.
    """
    result = await start_workflow(
        db=db,
        user_id=current_user.id,
        job_title=req.job_title,
        department=req.department,
        requirements=req.requirements,
        preferred_qualifications=req.preferred_qualifications,
        location=req.location,
        salary_range=req.salary_range,
    )
    return JobResponse(**result)


@router.get("")
async def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """List all active recruitment workflows."""
    return get_all_workflows(db)


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Get detailed status of a recruitment workflow."""
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return status


@router.post("/{job_id}/resumes")
async def upload_resume(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireHR],
    file: UploadFile = File(...),
):
    """Upload a candidate resume for a specific job requisition."""
    status = get_workflow_status(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
    if status["current_stage"] not in ["sourcing", "screening"]:
         raise HTTPException(status_code=400, detail=f"Cannot upload resumes in stage: {status['current_stage']}")

    # 1. Save uploaded file temporarily
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        try:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 2. Parse and index
    try:
        parsed = parse_resume_pdf(tmp_path)
        # Give candidate a unique ID for this job
        candidate_id = f"c_{uuid.uuid4().hex[:8]}"
        parsed["id"] = candidate_id
        
        # Override source file name to be original filename
        parsed["source_file"] = file.filename
        
        # Index into vector database
        index_resume(parsed)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    # 3. Advance workflow (trigger screening)
    # The scout agent usually finds candidates. Since we uploaded one, we'll
    # artificially add it to the state list and trigger the workflow.
    current_state = status.get("state", {})
    candidates = current_state.get("candidates", [])
    
    new_candidate = {
        "id": candidate_id,
        "name": parsed.get("name", "Unknown Candidate"),
        "email": parsed.get("email", ""),
        "skills": parsed.get("skills", []),
        "experience_years": parsed.get("experience_years", 0),
        "source": "manual_upload",
        "relevance_score": 1.0, # Given it's manually uploaded, we assume relevance
        "screening_score": 0,
        "screening_rationale": "",
        "status": "pending_review"
    }
    
    candidates.append(new_candidate)
    
    try:
        updated_state = await resume_workflow(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            action="upload_resume",
            state_updates={"candidates": candidates}
        )
        return {
            "status": "success",
            "message": f"Resume '{file.filename}' parsed and added to candidate pool.",
            "candidate": new_candidate,
            "current_stage": updated_state.get("current_stage")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow state: {e}")
