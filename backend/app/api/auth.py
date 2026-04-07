"""Auth API — login, register, and me endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.core.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    WS_TOKEN_AUDIENCE,
    hash_password,
    verify_password,
    create_access_token,
    create_ws_ticket,
    get_current_user,
    user_may_subscribe_job_ws,
)
from app.models.db_models import Job, User

router = APIRouter(prefix="/api/auth", tags=["Auth"])
COOKIE_NAME = "access_token"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    department: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    department: str | None
    is_active: bool


@router.post("/login", response_model=TokenResponse)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    response: Response,
):
    """Login and return a JWT access token."""
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    _set_session_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    req: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
    response: Response,
):
    """Register a new user account."""
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Self-registration always creates lowest-privileged users.
    user = User(
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role="viewer",
        department=req.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    _set_session_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
    )


@router.post("/logout")
async def logout(response: Response):
    _clear_session_cookie(response)
    return {"ok": True}


@router.get("/ws-ticket")
async def issue_ws_ticket(
    job_id: Annotated[str, Query(description="Job id to subscribe via WebSocket")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Mint a short-lived JWT for ``/ws/{job_id}?token=...`` (audience ``prohr-ws``).

    Use the **cookie session** for this HTTP call; do not put the long-lived access token in the
    WebSocket URL. Clients should call this endpoint again before reconnect if the ticket expires.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not user_may_subscribe_job_ws(current_user, job):
        raise HTTPException(status_code=403, detail="Not allowed to subscribe to this job")
    ticket = create_ws_ticket(
        current_user.id,
        job_id,
        settings.ws_ticket_expire_minutes,
    )
    return {
        "ticket": ticket,
        "aud": WS_TOKEN_AUDIENCE,
        "expires_in_seconds": settings.ws_ticket_expire_minutes * 60,
    }


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    """Return currently authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        department=current_user.department,
        is_active=current_user.is_active,
    )


@router.get("/users", tags=["Admin"])
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all users (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    users = db.query(User).all()
    return [
        {"id": u.id, "email": u.email, "full_name": u.full_name,
         "role": u.role, "department": u.department, "is_active": u.is_active,
         "last_login": u.last_login}
        for u in users
    ]
