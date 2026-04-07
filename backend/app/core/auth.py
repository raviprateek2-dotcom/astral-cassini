"""JWT authentication, password hashing, and RBAC dependencies."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import Job, User

# --- Config ---
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours
WS_TOKEN_AUDIENCE = "prohr-ws"

if len(SECRET_KEY) < 32 or not secrets.compare_digest(SECRET_KEY, SECRET_KEY.strip()):
    raise RuntimeError(
        "Invalid SECRET_KEY. Set a non-empty, 32+ character secret in environment."
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# --- Password helpers ---

def hash_password(plain: str) -> str:
    """Hashes a password using bcrypt."""
    pwd_bytes = plain.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plain password against a bcrypt hash."""
    pwd_bytes = plain.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)



# --- Token helpers ---

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_ws_ticket(user_id: int, job_id: str, expire_minutes: int) -> str:
    """Short-lived JWT for WebSocket query param only (aud={WS_TOKEN_AUDIENCE}, binds job_id)."""
    payload = {
        "sub": str(user_id),
        "aud": WS_TOKEN_AUDIENCE,
        "job_id": job_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def user_may_subscribe_job_ws(user: User, job: Job) -> bool:
    """Same visibility rule as app.api.websocket (HR roles or job owner)."""
    if user.role in {"admin", "hr_manager", "business_lead"}:
        return True
    owner_id = job.created_by_id
    if owner_id is None:
        return False
    return int(owner_id) == int(user.id)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- FastAPI dependencies ---

def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """Dependency — resolves the JWT token to a User ORM object."""
    cookie_token = request.cookies.get("access_token")
    effective_token = token or cookie_token
    if not effective_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(effective_token)
    user_id: int | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")
    return user


def require_role(*roles: str):
    """Dependency factory — checks that the current user has one of the given roles."""
    def _check(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted for this action.",
            )
        return current_user
    return _check


# Convenience role dependencies
RequireAdmin = Depends(require_role("admin"))
RequireHR = Depends(require_role("admin", "hr_manager"))
RequireBusinessLead = Depends(require_role("admin", "hr_manager", "business_lead"))
RequireAny = Depends(get_current_user)
