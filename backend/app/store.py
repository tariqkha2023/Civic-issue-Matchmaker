"""Persistent MVP schema. PostgreSQL in development; SQLite for isolated tests."""

import os
import time

from dotenv import load_dotenv
from sqlalchemy import (
    JSON,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
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


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String(1000), default="")
    read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[float] = mapped_column(Float, default=time.time, index=True)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[float] = mapped_column(Float, default=time.time, index=True)


class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    version: Mapped[int] = mapped_column(primary_key=True)
    applied_at: Mapped[float] = mapped_column(Float, default=time.time)


class SourceSettings(Base):
    __tablename__ = "source_settings"
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id"), primary_key=True
    )
    fields: Mapped[dict] = mapped_column(JSON, default=dict)


class IssueInfo(Base):
    __tablename__ = "issue_info"
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    fields: Mapped[dict] = mapped_column(JSON, default=dict)


class Contribution(Base):
    __tablename__ = "contributions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    state: Mapped[str]
    evidence: Mapped[str] = mapped_column(default="")
    note: Mapped[str] = mapped_column(default="")
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)
    events: Mapped[list] = mapped_column(JSON, default=list)


Index(
    "one_active_contribution_per_user_issue",
    Contribution.user_id,
    Contribution.task_id,
    unique=True,
    sqlite_where=Contribution.state.in_(["interested", "in_progress", "submitted"]),
    postgresql_where=Contribution.state.in_(["interested", "in_progress", "submitted"]),
)


class RelevanceFeedback(Base):
    __tablename__ = "relevance_feedback"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    relevant: Mapped[bool]
    explanation: Mapped[str] = mapped_column(default="")
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)


class AccountSettings(Base):
    __tablename__ = "account_settings"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)


class ScanRun(Base):
    __tablename__ = "scan_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id"), index=True
    )
    started_at: Mapped[float] = mapped_column(Float, default=time.time)
    finished_at: Mapped[float | None]
    status: Mapped[str]
    count: Mapped[int] = mapped_column(default=0)
    detail: Mapped[str] = mapped_column(default="")


class JobLease(Base):
    __tablename__ = "job_leases"
    name: Mapped[str] = mapped_column(primary_key=True)
    expires_at: Mapped[float] = mapped_column(Float, default=0)


class EventDelivery(Base):
    __tablename__ = "event_deliveries"
    key: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str]
    created_at: Mapped[float] = mapped_column(Float, default=time.time)


class IssueEnrichment(Base):
    __tablename__ = "issue_enrichments"
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    content_hash: Mapped[str]
    model: Mapped[str]
    fields: Mapped[dict] = mapped_column(JSON)
    cost: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)


class EnrichmentRun(Base):
    __tablename__ = "enrichment_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    fields: Mapped[dict] = mapped_column(JSON, default=dict)


class StagedIssue(Base):
    __tablename__ = "staged_issues"
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id"), primary_key=True
    )
    source_id: Mapped[str] = mapped_column(primary_key=True)
    fields: Mapped[dict] = mapped_column(JSON)


def make_engine(url=None):
    url = url or os.getenv("DATABASE_URL", "sqlite:///./civic-dev.db")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    result = create_engine(
        url,
        **(
            {"connect_args": {"check_same_thread": False}}
            if url.startswith("sqlite")
            else {}
        ),
    )

    if url.startswith("sqlite"):

        @event.listens_for(result, "connect")
        def configure_sqlite(connection, _):
            connection.execute("PRAGMA busy_timeout=30000")

    return result


engine = make_engine()


def get_db():
    with Session(engine) as db:
        yield db
