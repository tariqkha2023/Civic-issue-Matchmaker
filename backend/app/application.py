"""Application services: validated requests coordinating role and domain services."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts import Profile, current_user, user_view
from app.services import (
    assign_roles,
    can_maintain,
    change_participation,
    correct_metadata,
    require_admin,
)
from app.store import (
    ActiveClaim,
    AuditEntry,
    ParticipationEvent,
    Repository,
    Task,
    User,
    get_db,
)
from app.views import task_view

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(current_user)]


class ParticipationInput(BaseModel):
    action: Literal["claimed", "released", "completed"]


@router.post("/tasks/{task_id}/participation")
def participate(task_id: int, body: ParticipationInput, user: Actor, db: DB):
    change_participation(db, user, task_id, body.action)
    task = db.get(Task, task_id)
    return task_view(
        task,
        db.get(Repository, task.repository_id),
        profile=user.profile,
        db=db,
        user=user,
    )


@router.get("/me/participation")
def history(user: Actor, db: DB):
    active = []
    for claim in db.scalars(select(ActiveClaim).where(ActiveClaim.user_id == user.id)):
        task = db.get(Task, claim.task_id)
        active.append(
            task_view(
                task,
                db.get(Repository, task.repository_id),
                profile=user.profile,
                db=db,
                user=user,
            )
        )
    events = [
        {
            "id": e.id,
            "task_id": e.task_id,
            "title": db.get(Task, e.task_id).title,
            "action": e.action,
            "occurred_at": e.occurred_at,
        }
        for e in db.scalars(
            select(ParticipationEvent)
            .where(ParticipationEvent.user_id == user.id)
            .order_by(ParticipationEvent.id.desc())
        )
    ]
    return {"active": active, "events": events}


class MetadataInput(BaseModel):
    skills: list[str] = Field(default_factory=list, max_length=30)
    topics: list[str] = Field(default_factory=list, max_length=30)
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] | None = None
    effort: float | None = Field(default=None, ge=0, le=10000, allow_inf_nan=False)

    @field_validator("skills", "topics")
    @classmethod
    def clean_entries(cls, values):
        return Profile.clean_lists(values)


@router.get("/maintainer/tasks")
def maintainer_tasks(user: Actor, db: DB):
    from app.services import roles

    if not set(roles(db, user)) & {"maintainer", "administrator"}:
        raise HTTPException(403, "Maintainer access required.")
    return [
        task_view(task, repo, profile=user.profile, db=db, user=user)
        for task, repo in db.execute(
            select(Task, Repository).join(Repository).order_by(Task.id.desc())
        )
        if can_maintain(db, user, repo.id)
    ]


@router.put("/maintainer/tasks/{task_id}/metadata")
def metadata(task_id: int, body: MetadataInput, user: Actor, db: DB):
    task = correct_metadata(db, user, task_id, body.model_dump())
    return task_view(
        task,
        db.get(Repository, task.repository_id),
        profile=user.profile,
        db=db,
        user=user,
    )


@router.get("/admin/users")
def users(user: Actor, db: DB):
    require_admin(db, user)
    return [user_view(u, db) for u in db.scalars(select(User).order_by(User.id))]


class RoleInput(BaseModel):
    roles: list[Literal["maintainer", "administrator"]] = Field(
        default_factory=list, max_length=2
    )
    repository_ids: list[int] = Field(default_factory=list, max_length=100)


@router.put("/admin/users/{user_id}/roles")
def update_roles(user_id: int, body: RoleInput, user: Actor, db: DB):
    target = assign_roles(db, user, user_id, body.roles, body.repository_ids)
    return user_view(target, db)


@router.get("/admin/repositories")
def sources(user: Actor, db: DB):
    require_admin(db, user)
    return [
        {
            "id": r.id,
            "path": r.path,
            "source": r.source,
            "enabled": r.enabled,
            "last_success": r.last_success,
            "error": r.scan_error,
        }
        for r in db.scalars(select(Repository).order_by(Repository.id))
    ]


class SourceInput(BaseModel):
    enabled: bool


@router.put("/admin/repositories/{repository_id}")
def update_source(repository_id: int, body: SourceInput, user: Actor, db: DB):
    require_admin(db, user)
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(404, "Repository not found.")
    repo.enabled = body.enabled
    db.add(
        AuditEntry(
            actor_id=user.id,
            action="source.updated",
            target=f"repository:{repo.id}",
            details=body.model_dump(),
        )
    )
    db.commit()
    return {"id": repo.id, "enabled": repo.enabled}


@router.get("/admin/audit")
def audit(user: Actor, db: DB):
    require_admin(db, user)
    return [
        {
            "id": e.id,
            "actor_id": e.actor_id,
            "action": e.action,
            "target": e.target,
            "details": e.details,
            "occurred_at": e.occurred_at,
        }
        for e in db.scalars(
            select(AuditEntry).order_by(AuditEntry.id.desc()).limit(100)
        )
    ]
