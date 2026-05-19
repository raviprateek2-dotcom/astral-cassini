"""Webhooks Router for Phase 4.4.2: SendGrid Inbound Parse."""

import logging
from fastapi import APIRouter, Request, BackgroundTasks
from app.models.state import PipelineStage
from app.core.database import SessionLocal
from app.models.db_models import Job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

async def _process_inbound_email(to_email: str, from_email: str, subject: str, text_body: str):
    """Background task to process candidate replies and wake up the Response Tracker."""
    logger.info(f"Processing inbound email from {from_email} regarding {subject}")
    
    # In a real system, you'd match `from_email` to the candidate in the DB.
    # For this demo, we'll just log it. If matched, we would update the DB state
    # and trigger the orchestrator's `response_tracker_node`.
    
    with SessionLocal() as db:
        # Pseudo-code for matching:
        # candidate = db.query(Candidate).filter_by(email=from_email).first()
        # if candidate:
        #     job_state = db.query(JobState).filter_by(job_id=candidate.job_id).first()
        #     job_state.current_stage = PipelineStage.ENGAGEMENT.value
        #     ... save and wake up orchestrator ...
        pass
    
    logger.info(f"Webhook processing complete for {from_email}.")


@router.post("/inbound-email", status_code=202)
async def sendgrid_inbound_parse(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint for SendGrid Inbound Parse.
    SendGrid posts form-data here when a candidate replies to an outreach email.
    """
    try:
        form_data = await request.form()
        
        # SendGrid specific fields
        to_email = form_data.get("to", "")
        from_email = form_data.get("from", "")
        subject = form_data.get("subject", "")
        text_body = form_data.get("text", "")

        # Offload the LLM sentiment parsing and state updating to a background task
        # so we can immediately return 202 Accepted to SendGrid (required by their SLA).
        background_tasks.add_task(
            _process_inbound_email,
            str(to_email),
            str(from_email),
            str(subject),
            str(text_body)
        )
        
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Failed to parse inbound webhook: {e}")
        return {"status": "error", "message": "Failed to parse"}
