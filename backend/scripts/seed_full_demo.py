import os
import random
import uuid
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

from app.core.database import SessionLocal
from app.models.db_models import Job, User, CandidateScore, Interview, AuditEvent, Recommendation, Outreach, Offer

first_names = ["Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia", "James", "Isabella", "Oliver"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

def generate_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

roles = [
    ("Senior Frontend Engineer", "Engineering"),
    ("Backend Developer", "Engineering"),
    ("Product Manager", "Product"),
    ("UX Designer", "Design"),
    ("Data Scientist", "Data")
]

def seed():
    db = SessionLocal()
    try:
        # We will NOT delete the existing jobs, we'll just add 5 fully fleshed out "completed" or "hire_review" pipelines
        admin_user = db.query(User).filter(User.role == "admin").first()
        admin_id = admin_user.id if admin_user else None

        for _ in range(5):
            role_title, dept = random.choice(roles)
            job_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
            stage = random.choice(["completed", "hire_review", "offer"])
            
            job = Job(
                job_id=job_id,
                job_title=role_title,
                department=dept,
                location="Remote",
                current_stage=stage,
                created_by_id=admin_id,
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(5, 30)),
                requirements=["Python", "React", "TypeScript", "AWS", "SQL"],
                workflow_state={}
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            # Audit Events
            events = [
                ("Architect", "Drafted Job Description", "intake"),
                ("Critic", "Reviewed Job Description", "jd_review"),
                ("Scout", "Sourced 3 Candidates", "sourcing"),
                ("Screener", "Scored Candidates", "screening"),
                ("Outreach", "Sent Emails", "outreach"),
                ("Coordinator", "Scheduled Interviews", "scheduling"),
                ("Interviewer", "Conducted Technical Interviews", "interviewing"),
                ("Decider", "Generated Recommendations", "decision")
            ]
            
            base_time = job.created_at
            for idx, (agent, action, stg) in enumerate(events):
                db.add(AuditEvent(
                    job_id=job_id,
                    agent=agent,
                    action=action,
                    details=f"Agent {agent} successfully executed {action} with 100% confidence. Extracted parameters and moved pipeline forward.",
                    stage=stg,
                    timestamp=base_time + timedelta(hours=idx * 4)
                ))

            # Candidates
            for i in range(3):
                c_id = f"CAND-{uuid.uuid4().hex[:6].upper()}"
                c_name = generate_name()

                # Score
                db.add(CandidateScore(
                    job_id=job_id,
                    candidate_id=c_id,
                    candidate_name=c_name,
                    overall_score=round(random.uniform(75, 98), 1),
                    match_percentage=round(random.uniform(75, 98), 1),
                    skills_match=round(random.uniform(75, 100), 1),
                    experience_match=round(random.uniform(60, 100), 1),
                    education_match=round(random.uniform(80, 100), 1),
                    cultural_fit=round(random.uniform(70, 100), 1),
                    strengths=["Strong technical background", "Great communication skills", "Proven leadership in past roles"],
                    gaps=["Lacks extensive management experience"],
                    missing_skills=["Kubernetes"],
                    overqualification=[],
                    reasoning=f"{c_name} exhibits strong alignment with the core responsibilities, though there are minor gaps in infrastructure tooling."
                ))

                # Outreach
                db.add(Outreach(
                    job_id=job_id,
                    candidate_id=c_id,
                    candidate_name=c_name,
                    email_subject=f"Interview Request: {role_title} at PRO HR",
                    email_body=f"Hi {c_name}, your profile stood out to us...",
                    response_text="Thank you! I am very interested and available next Tuesday.",
                    engagement_level="High",
                    status="responding"
                ))

                # Interview
                db.add(Interview(
                    job_id=job_id,
                    candidate_id=c_id,
                    candidate_name=c_name,
                    interview_type="technical",
                    status="completed",
                    overall_score=round(random.uniform(7.0, 9.5), 1),
                    technical_score=round(random.uniform(7.0, 9.5), 1),
                    communication_score=round(random.uniform(7.0, 9.5), 1),
                    problem_solving_score=round(random.uniform(7.0, 9.5), 1),
                    cultural_fit_score=round(random.uniform(7.0, 9.5), 1),
                    key_observations=["Solved the dynamic programming problem efficiently", "Very articulate when explaining architecture"],
                    concerns=["Slightly hesitant on distributed systems edge cases"]
                ))

                # Recommendation
                decisions = ["hire", "hire", "no_hire"]
                decision = decisions[i]
                db.add(Recommendation(
                    job_id=job_id,
                    candidate_id=c_id,
                    candidate_name=c_name,
                    decision=decision,
                    confidence=round(random.uniform(0.7, 0.95), 2),
                    overall_weighted_score=round(random.uniform(75, 95), 1),
                    reasoning=f"Based on the aggregate screening and interview scores, {c_name} is marked as a {decision}.",
                    risk_factors=["Potential flight risk due to commute distance"] if decision == "no_hire" else []
                ))

            db.commit()

        print("Successfully generated deep pipelines with candidates, interviews, decisions, and audit trails.")
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
