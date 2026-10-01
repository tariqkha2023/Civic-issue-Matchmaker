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

