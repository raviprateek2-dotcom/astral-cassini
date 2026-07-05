import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

from app.core.database import SessionLocal
from app.models.db_models import Job, User

stages = [
    "intake",
    "jd_drafting",
    "jd_review",
    "sourcing",
    "screening",
    "shortlist_review",
    "outreach",
    "engagement",
    "scheduling",
    "interviewing",
    "decision",
    "hire_review",
    "offer",
    "completed"
]

roles = [
    ("Senior Frontend Engineer", "Engineering"),
    ("Backend Developer", "Engineering"),
    ("Product Manager", "Product"),
    ("UX Designer", "Design"),
    ("Data Scientist", "Data"),
    ("Marketing Director", "Marketing"),
    ("Sales Executive", "Sales"),
    ("HR Specialist", "Human Resources"),
    ("DevOps Engineer", "Engineering"),
    ("Customer Success Rep", "Customer Success")
]

def seed():
    db = SessionLocal()
    try:
        # Ensure we have a user
        admin_user = db.query(User).filter(User.role == "admin").first()
        admin_id = admin_user.id if admin_user else None

        # Create 10 pipelines with different stages
        created = 0
        for i in range(10):
            role_title, dept = roles[i % len(roles)]
            stage = random.choice(stages)
            
            job_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
            
            job = Job(
                job_id=job_id,
                job_title=role_title,
                department=dept,
                location="Remote",
                current_stage=stage,
                created_by_id=admin_id,
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 14)),
                requirements=["Python", "React", "AWS"] if "Engineer" in role_title else ["Communication", "Strategy"],
                workflow_state={}
            )
            
            if stage in ["completed", "offer", "hire_review", "decision"]:
                job.candidates_count = random.randint(10, 50)
            elif stage in ["interviewing", "scheduling", "engagement", "outreach"]:
                job.candidates_count = random.randint(5, 20)
            elif stage in ["shortlist_review", "screening", "sourcing"]:
                job.candidates_count = random.randint(0, 10)
            else:
                job.candidates_count = 0
                
            db.add(job)
            created += 1

        db.commit()
        print(f"Successfully seeded {created} pipelines across various stages.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
