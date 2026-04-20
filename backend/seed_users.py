import os
from dotenv import load_dotenv

load_dotenv()

from app.core.database import SessionLocal
from app.models.db_models import User
from app.core.auth import hash_password

def seed():
    db = SessionLocal()
    try:
        # Admin User
        if not db.query(User).filter(User.email == "admin@prohr.ai").first():
            db.add(User(
                email="admin@prohr.ai",
                full_name="System Admin",
                hashed_password=hash_password("password123"),
                role="admin"
            ))
            print("Seeded admin@prohr.ai")
        else:
            print("admin@prohr.ai already exists")

        # HR User
        if not db.query(User).filter(User.email == "hr@prohr.ai").first():
            db.add(User(
                email="hr@prohr.ai",
                full_name="HR Manager",
                hashed_password=hash_password("password123"),
                role="hr_manager",
                department="Engineering"
            ))
            print("Seeded hr@prohr.ai")
        else:
            print("hr@prohr.ai already exists")

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
