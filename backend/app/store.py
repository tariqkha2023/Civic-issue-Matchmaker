"""Persistent MVP schema. PostgreSQL in development; SQLite for isolated tests."""

import os
import time

from dotenv import load_dotenv
from sqlalchemy import JSON, Float, ForeignKey, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

load_dotenv()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str]
    profile: Mapped[dict] = mapped_column(JSON, default=dict)


class LoginSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    last_activity: Mapped[float] = mapped_column(Float, default=time.time)


class Repository(Base):
    __tablename__ = "repositories"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str]
    path: Mapped[str]
    enabled: Mapped[bool] = mapped_column(default=True)
    selection_labels: Mapped[list] = mapped_column(JSON, default=list)
    last_success: Mapped[float | None]
    scan_error: Mapped[str | None]
    __table_args__ = (UniqueConstraint("source", "path"),)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id"), index=True
    )
    source_id: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    url: Mapped[str]
    status: Mapped[str] = mapped_column(index=True)
    labels: Mapped[list] = mapped_column(JSON)
    metadata_fields: Mapped[dict] = mapped_column(JSON)
    first_seen: Mapped[float] = mapped_column(Float, default=time.time)
    __table_args__ = (UniqueConstraint("repository_id", "source_id"),)


class SavedTask(Base):
    __tablename__ = "saved_tasks"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    saved_at: Mapped[float] = mapped_column(Float, default=time.time)


class AuthEvent(Base):
    __tablename__ = "auth_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    occurred_at: Mapped[float] = mapped_column(Float, default=time.time, index=True)
    client_hash: Mapped[str] = mapped_column(index=True)
    subject_hash: Mapped[str] = mapped_column(index=True)
    operation: Mapped[str]
    success: Mapped[bool]
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class AccountRole(Base):
    __tablename__ = "account_roles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(primary_key=True)


class MaintainerAccess(Base):
    __tablename__ = "maintainer_access"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id"), primary_key=True
    )


class ActiveClaim(Base):
    __tablename__ = "active_claims"
    # The task primary key enforces one active claimant across all requests.
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    claimed_at: Mapped[float] = mapped_column(Float, default=time.time)


class ParticipationEvent(Base):
    __tablename__ = "participation_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str]
    occurred_at: Mapped[float] = mapped_column(Float, default=time.time)


class MetadataCorrection(Base):
    __tablename__ = "metadata_corrections"
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    fields: Mapped[dict] = mapped_column(JSON)


class AuditEntry(Base):
    __tablename__ = "audit_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str]
    target: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[float] = mapped_column(Float, default=time.time)


class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    version: Mapped[int] = mapped_column(primary_key=True)
    applied_at: Mapped[float] = mapped_column(Float, default=time.time)


def make_engine(url=None):
    url = url or os.getenv("DATABASE_URL", "sqlite:///./civic-dev.db")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(
        url,
        **(
            {"connect_args": {"check_same_thread": False}}
            if url.startswith("sqlite")
            else {}
        ),
    )


engine = make_engine()


def get_db():
    with Session(engine) as db:
        yield db
