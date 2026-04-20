import os
from dotenv import load_dotenv

load_dotenv()

from app.core.database import SessionLocal
from app.models.db_models import User
from app.core.auth import hash_password

def reset_passwords():
    db = SessionLocal()
    try:
        new_hash = hash_password("password123")
        users = db.query(User).filter(User.email.in_(["admin@prohr.ai", "hr@prohr.ai"])).all()
        for user in users:
            user.hashed_password = new_hash
            print(f"Reset password for {user.email}")
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    reset_passwords()
