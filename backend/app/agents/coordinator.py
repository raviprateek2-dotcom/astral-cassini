"""Agent 5: The Coordinator — Interview scheduling.

Takes the approved shortlist and generates interview schedules
using mock calendar and email tools.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.models.state import RecruitmentState, PipelineStage
from app.tools.calendar_tool import schedule_meeting
from app.tools.email_tool import send_interview_invitation


def create_coordinator():
    """Create The Coordinator agent node function."""

    def coordinator_node(state: RecruitmentState) -> dict:
        """Schedule interviews for approved shortlisted candidates."""

        scored_candidates = state.get("scored_candidates", [])
        job_title = state.get("job_title", "")

        if not scored_candidates:
            return {
                "error": "No scored candidates for scheduling",
                "audit_log": [{
                    "timestamp": datetime.now().isoformat(),
                    "agent": "The Coordinator",
                    "action": "error",
                    "details": "No candidates available for interview scheduling",
                    "stage": PipelineStage.SCHEDULING.value,
                }],
            }

        # Take top candidates (score >= 60 or top 5)
        top_candidates = [
            c for c in scored_candidates
            if c.get("overall_score", 0) >= 60
        ][:5]

        if not top_candidates:
            top_candidates = scored_candidates[:3]

        scheduled_interviews = []
        base_time = datetime.now() + timedelta(days=2)

        for i, candidate in enumerate(top_candidates):
            # Schedule technical interview
            interview_time = base_time + timedelta(days=i, hours=10)

            interview = {
                "id": f"int-{candidate.get('candidate_id', i)}-tech",
                "candidate_id": candidate.get("candidate_id", ""),
                "candidate_name": candidate.get("candidate_name", "Unknown"),
                "interview_type": "technical",
                "scheduled_time": interview_time.isoformat(),
                "duration_minutes": 60,
                "interviewers": ["Tech Lead", "Senior Engineer"],
                "meeting_link": f"https://meet.example.com/interview-{i+1}",
                "status": "scheduled",
            }

            # Use mock tools
            schedule_meeting(
                title=f"Technical Interview: {candidate.get('candidate_name', '')} - {job_title}",
                time=interview_time.isoformat(),
                duration=60,
                attendees=[candidate.get("candidate_name", "")],
            )

            send_interview_invitation(
                to_email=f"{candidate.get('candidate_name', '').lower().replace(' ', '.')}@email.com",
                candidate_name=candidate.get("candidate_name", ""),
                job_title=job_title,
                interview_time=interview_time.isoformat(),
                meeting_link=interview["meeting_link"],
            )

            scheduled_interviews.append(interview)

            # Also schedule a behavioral interview
            behavioral_time = interview_time + timedelta(hours=3)
            behavioral_interview = {
                "id": f"int-{candidate.get('candidate_id', i)}-behav",
                "candidate_id": candidate.get("candidate_id", ""),
                "candidate_name": candidate.get("candidate_name", "Unknown"),
                "interview_type": "behavioral",
                "scheduled_time": behavioral_time.isoformat(),
                "duration_minutes": 45,
                "interviewers": ["HR Manager", "Department Head"],
                "meeting_link": f"https://meet.example.com/behavioral-{i+1}",
                "status": "scheduled",
            }
            scheduled_interviews.append(behavioral_interview)

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "The Coordinator",
            "action": "scheduled_interviews",
            "details": f"Scheduled {len(scheduled_interviews)} interviews for {len(top_candidates)} candidates",
            "stage": PipelineStage.SCHEDULING.value,
        }

        return {
            "scheduled_interviews": scheduled_interviews,
            "current_stage": PipelineStage.INTERVIEWING.value,
            "audit_log": [audit_entry],
        }

    return coordinator_node
