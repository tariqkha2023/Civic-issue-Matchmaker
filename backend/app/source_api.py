"""Project directory and administrator source controls."""

import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.application import DB, Actor
from app.projects import project_view, settings, validate_path
from app.services import can_maintain, require_admin
from app.store import (
    AuditEntry,
    MetadataCorrection,
    Repository,
    ScanRun,
    SourceSettings,
    Task,
)

router = APIRouter(prefix="/api")


@router.get("/admin/enrichment")
def enrichment_status(user: Actor, db: DB):
    require_admin(db, user)
    from app.enrichment import MODEL, cached_fields, project_context
    from app.store import EnrichmentRun, IssueEnrichment, JobLease

    cached = {r.task_id: r for r in db.scalars(select(IssueEnrichment))}
    tasks = list(
        db.scalars(
            select(Task)
            .join(Repository)
            .where(
                Task.status == "open",
                Repository.source == "github",
                Repository.enabled.is_(True),
            )
        )
    )
    projects = {
        r.repository_id: project_context(r.fields)
        for r in db.scalars(select(SourceSettings))
    }
    valid = [
        cached_fields(t, cached.get(t.id), projects.get(t.repository_id, {}))
        for t in tasks
    ]
    lease = db.get(JobLease, "issue-enrichment")
    latest = db.scalar(select(EnrichmentRun).order_by(EnrichmentRun.id.desc()).limit(1))
    return {
        "model": MODEL,
        "open_issues": len(tasks),
        "processed": sum(bool(f) for f in valid),
        "with_skills": sum(bool(f.get("skills")) for f in valid),
        "rejected": sum(f.get("status") == "rejected" for f in valid),
        "running": bool(lease and lease.expires_at > time.time()),
        "latest_run": latest.fields if latest else None,
    }


@router.get("/projects")
def projects(user: Actor, db: DB):
    return [
        project_view(db, repo)
        for repo in db.scalars(
            select(Repository)
            .where(Repository.source == "github", Repository.enabled.is_(True))
            .order_by(Repository.path)
        )
    ]


class SourceInput(BaseModel):
    path: str = Field(min_length=3, max_length=100)
    name: str = Field(default="", max_length=100)
    mission: str = Field(default="", max_length=2000)
    topics: list[str] = Field(default_factory=list, max_length=20)
    interval_minutes: int = Field(default=60, ge=60, le=10080)


@router.post("/admin/sources", status_code=201)
def add_source(body: SourceInput, user: Actor, db: DB):
    require_admin(db, user)
    path = validate_path(body.path.strip())
    if db.scalar(
        select(Repository).where(
            Repository.source == "github", Repository.path.ilike(path)
        )
    ):
        raise HTTPException(409, "Repository already configured.")
    repo = Repository(source="github", path=path)
    db.add(repo)
    db.flush()
    db.add(
        SourceSettings(
            repository_id=repo.id,
            fields={
                "name": body.name or path,
                "mission": body.mission,
                "topics": [t.strip().lower()[:100] for t in body.topics if t.strip()],
                "interval_minutes": body.interval_minutes,
            },
        )
    )
    db.add(
        AuditEntry(
            actor_id=user.id,
            action="source.added",
            target=f"repository:{repo.id}",
            details={"path": path},
        )
    )
    db.commit()
    return project_view(db, repo)


class ScheduleInput(BaseModel):
    interval_minutes: int = Field(ge=60, le=10080)
    topics: list[str] = Field(default_factory=list, max_length=20)
    name: str = Field(max_length=100)
    mission: str = Field(default="", max_length=2000)


@router.put("/admin/sources/{repository_id}/settings")
def update_settings(repository_id: int, body: ScheduleInput, user: Actor, db: DB):
    require_admin(db, user)
    repo = db.get(Repository, repository_id)
    if not repo or repo.source != "github":
        raise HTTPException(404, "GitHub source not found.")
    row = db.get(SourceSettings, repo.id)
    if not row:
        row = SourceSettings(repository_id=repo.id)
        db.add(row)
    row.fields = {**settings(db, repo), **body.model_dump(), "next_due": time.time()}
    db.add(
        AuditEntry(
            actor_id=user.id,
            action="source.settings",
            target=f"repository:{repo.id}",
            details=body.model_dump(),
        )
    )
    db.commit()
    return project_view(db, repo)


@router.post("/admin/sources/{repository_id}/scan", status_code=202)
def request_scan(repository_id: int, user: Actor, db: DB):
    require_admin(db, user)
    repo = db.get(Repository, repository_id)
    if not repo or repo.source != "github" or not repo.enabled:
        raise HTTPException(409, "Choose an enabled GitHub source.")
    row = db.get(SourceSettings, repo.id)
    if not row:
        row = SourceSettings(repository_id=repo.id)
        db.add(row)
    config = settings(db, repo)
    # Resuming retains its staged pages. An idle source gets a full reconciliation.
    row.fields = {
        **config,
        "next_due": time.time(),
        "force_full": not bool(config.get("cursor")),
    }
    db.add(
        AuditEntry(
            actor_id=user.id,
            action="source.scan_requested",
            target=f"repository:{repo.id}",
            details={},
        )
    )
    db.commit()
    return {
        "status": "queued",
        "detail": "Worker picks up scans within 15 seconds. Partial scans resume their saved pages.",
    }


@router.get("/admin/scans")
def scans(user: Actor, db: DB):
    require_admin(db, user)
    return [
        {
            "id": r.id,
            "repository_id": r.repository_id,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "status": r.status,
            "count": r.count,
            "detail": r.detail,
        }
        for r in db.scalars(select(ScanRun).order_by(ScanRun.id.desc()).limit(100))
    ]


@router.delete("/maintainer/tasks/{task_id}/metadata", status_code=204)
def reset_metadata(task_id: int, user: Actor, db: DB):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Issue not found.")
    if not can_maintain(db, user, task.repository_id):
        raise HTTPException(403, "Curator access required for this project.")
    row = db.get(MetadataCorrection, task_id)
    if row:
        db.add(
            AuditEntry(
                actor_id=user.id,
                action="metadata.reset",
                target=f"task:{task_id}",
                details={"before": row.fields},
            )
        )
        db.delete(row)
        db.commit()


@router.get("/curator/issues")
def curator_issues(user: Actor, db: DB, q: str = "", page: int = 1):
    from sqlalchemy import func

    from app.services import roles
    from app.store import MaintainerAccess
    from app.views import projection_context, task_view

    if not {"maintainer", "administrator"} & set(roles(db, user)):
        raise HTTPException(403, "Curator access required.")
    statement = (
        select(Task, Repository).join(Repository).where(Repository.source == "github")
    )
    if "administrator" not in roles(db, user):
        scopes = select(MaintainerAccess.repository_id).where(
            MaintainerAccess.user_id == user.id
        )
        statement = statement.where(Repository.id.in_(scopes))
    if q:
        statement = statement.where(Task.title.ilike("%" + q[:200] + "%"))
    count = db.scalar(select(func.count()).select_from(statement.subquery()))
    candidates = list(
        db.execute(
            statement.order_by(Task.id.desc()).offset((max(1, page) - 1) * 20).limit(20)
        )
    )
    context = projection_context(db, user, [t.id for t, _ in candidates])
    return {
        "items": [
            task_view(t, r, profile=user.profile, db=db, user=user, context=context)
            for t, r in candidates
        ],
        "total": count,
    }
