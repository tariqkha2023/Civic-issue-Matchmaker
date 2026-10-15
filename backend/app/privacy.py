"""Account export, preferences and immediate reauthenticated anonymization."""

import secrets

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, or_, select

from app.application import DB, Actor
from app.events import preferences
from app.security import hash_password, verify_password
from app.store import (
    AccountRole,
    AccountSettings,
    ActiveClaim,
    AuditEntry,
    AuthEvent,
    Contribution,
    EventDelivery,
    LoginSession,
    MaintainerAccess,
    Message,
    Notification,
    ParticipationEvent,
    RelevanceFeedback,
    SavedTask,
)

router = APIRouter(prefix="/api")


class PreferencesInput(BaseModel):
    new_matches: bool = True
    activity: bool = True
    minimum_score: float = Field(default=60, ge=0, le=100)


@router.get("/me/preferences")
def get_preferences(user: Actor, db: DB):
    return preferences(db, user.id)


@router.put("/me/preferences")
def set_preferences(body: PreferencesInput, user: Actor, db: DB):
    row = db.get(AccountSettings, user.id)
    if not row:
        row = AccountSettings(user_id=user.id)
        db.add(row)
    row.preferences = body.model_dump()
    db.commit()
    return row.preferences


@router.get("/me/export")
def export(user: Actor, db: DB):
    def rows(model, condition):
        return [
            {
                column.name: getattr(row, column.name)
                for column in model.__table__.columns
            }
            for row in db.scalars(select(model).where(condition))
        ]

    return {
        "account": {"id": user.id, "email": user.email, "profile": user.profile},
        "preferences": preferences(db, user.id),
        "saved": rows(SavedTask, SavedTask.user_id == user.id),
        "contributions": rows(Contribution, Contribution.user_id == user.id),
        "legacy_history": rows(
            ParticipationEvent, ParticipationEvent.user_id == user.id
        ),
        "feedback": rows(RelevanceFeedback, RelevanceFeedback.user_id == user.id),
        "notifications": rows(Notification, Notification.user_id == user.id),
        "messages": rows(
            Message, or_(Message.sender_id == user.id, Message.recipient_id == user.id)
        ),
    }


class DeleteInput(BaseModel):
    password: str = Field(min_length=1, max_length=128)


@router.delete("/me", status_code=204)
def delete_account(body: DeleteInput, response: Response, user: Actor, db: DB):
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            403, "Re-enter your current password to delete the account."
        )
    from app.services import roles

    if "administrator" in roles(db, user):
        # Reuse role administration's serialized last-admin rule.
        from app.services import assign_roles

        assign_roles(db, user, user.id, [], [], commit=False)
    uid = user.id
    for model in [
        AccountSettings,
        ActiveClaim,
        AccountRole,
        Contribution,
        EventDelivery,
        LoginSession,
        MaintainerAccess,
        Notification,
        ParticipationEvent,
        RelevanceFeedback,
        SavedTask,
    ]:
        db.execute(delete(model).where(model.user_id == uid))
    db.execute(
        delete(Message).where(
            or_(Message.sender_id == uid, Message.recipient_id == uid)
        )
    )
    db.execute(delete(AuthEvent).where(AuthEvent.actor_id == uid))
    for event in db.scalars(
        select(AuditEntry).where(
            or_(AuditEntry.actor_id == uid, AuditEntry.target == f"user:{uid}")
        )
    ):
        event.details = {"anonymized": True}
    user.email = f"deleted-{uid}-{secrets.token_hex(8)}@invalid.local"
    user.profile = {
        "name": "Deleted account",
        "skills": [],
        "interests": [],
        "repositories": [],
        "level": "Beginner",
        "difficulty": "Beginner",
        "hours": 0,
        "deleted": True,
    }
    user.password_hash = hash_password(secrets.token_urlsafe(40))
    db.add(
        AuditEntry(
            actor_id=uid,
            action="account.anonymized",
            target=f"user:{uid}",
            details={"anonymized": True},
        )
    )
    db.commit()
    response.delete_cookie("civic_session", path="/")
