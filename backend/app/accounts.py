"""Account domain operations and authenticated request dependency."""

import os
import re
import secrets
import time
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.security import token_hash
from app.services import roles
from app.store import AuthEvent, LoginSession, MaintainerAccess, User, get_db


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class Registration(Credentials):
    name: str = Field(min_length=2, max_length=100)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Enter your name")
        return value.strip()


class Profile(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    skills: list[str] = Field(default_factory=list, max_length=30)
    interests: list[str] = Field(default_factory=list, max_length=30)
    level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    hours: float = Field(default=0, ge=0, le=168)
    repositories: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("skills", "interests", "repositories")
    @classmethod
    def clean_lists(cls, values):
        if any(not value.strip() or len(value) > 100 for value in values):
            raise ValueError("Each entry must contain 1–100 characters")
        return list(dict.fromkeys(value.strip().lower() for value in values))

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Enter your name")
        return value.strip()


def current_user(request: Request, db: Annotated[Session, Depends(get_db)]):
    token = request.cookies.get("civic_session")
    session = db.get(LoginSession, token_hash(token)) if token else None
    if not session:
        raise HTTPException(401, "Please sign in.")
    if time.time() - session.last_activity >= 1800:
        db.delete(session)
        db.commit()
        raise HTTPException(401, "Session expired. Please sign in again.")
    session.last_activity = time.time()
    db.commit()
    return db.get(User, session.user_id)


def user_view(user, db):
    return {
        "id": user.id,
        "email": user.email,
        "profile": user.profile,
        "roles": roles(db, user),
        "maintained_repositories": list(
            db.scalars(
                select(MaintainerAccess.repository_id).where(
                    MaintainerAccess.user_id == user.id
                )
            )
        ),
    }


def establish_session(db, user, response):
    token = secrets.token_urlsafe(32)
    db.add(LoginSession(token_hash=token_hash(token), user_id=user.id))
    db.commit()
    response.set_cookie(
        "civic_session",
        token,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        path="/",
    )
    return user_view(user, db)


def auth_keys(request, email):
    client = request.client.host if request.client else "unknown"
    return token_hash(client), token_hash(email)


def check_auth_limit(db, request, email):
    client_key, subject_key = auth_keys(request, email)
    recent = time.time() - 900
    attempts = db.scalar(
        select(func.count())
        .select_from(AuthEvent)
        .where(AuthEvent.client_hash == client_key, AuthEvent.occurred_at > recent)
    )
    failures = db.scalar(
        select(func.count())
        .select_from(AuthEvent)
        .where(
            AuthEvent.subject_hash == subject_key,
            AuthEvent.occurred_at > recent,
            AuthEvent.success.is_(False),
        )
    )
    if attempts >= 30 or failures >= 10:
        raise HTTPException(
            429,
            "Too many authentication attempts. Try again in 15 minutes.",
            headers={"Retry-After": "900"},
        )


def record_auth(db, request, email, operation, success, actor_id=None):
    client_key, subject_key = auth_keys(request, email)
    db.add(
        AuthEvent(
            client_hash=client_key,
            subject_hash=subject_key,
            operation=operation,
            success=success,
            actor_id=actor_id,
        )
    )
    db.commit()
