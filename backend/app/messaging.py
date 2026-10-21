"""In-app notifications and direct messages between accounts."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.accounts import current_user
from app.services import roles
from app.store import Message, Notification, User, get_db

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(current_user)]
STAFF = {"maintainer", "administrator"}


def notify(db: Session, user_id: int, title: str, body: str = "") -> None:
    """Queue a notification. The caller commits it with its own transaction."""
    from uuid import uuid4

    from app.events import deliver
    deliver(db, user_id, "event:" + uuid4().hex, title, body, "activity")


def notification_view(n: Notification):
    return {
        "id": n.id,
        "title": n.title,
        "body": n.body,
        "read": n.read,
        "created_at": n.created_at,
    }


def message_view(m: Message, me: int):
    return {
        "id": m.id,
        "body": m.body,
        "mine": m.sender_id == me,
        "read": m.read,
        "created_at": m.created_at,
    }


def display_name(user: User) -> str:
    return (user.profile or {}).get("name") or user.email.split("@")[0]


def unread_counts(db: Session, user: User):
    return {
        "notifications": db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.read.is_(False))
        ),
        "messages": db.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.recipient_id == user.id, Message.read.is_(False))
        ),
    }


@router.get("/me/unread")
def unread(user: Actor, db: DB):
    return unread_counts(db, user)


@router.get("/me/notifications")
def list_notifications(user: Actor, db: DB, limit: int = Query(50, ge=1, le=200)):
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
    )
    return [notification_view(n) for n in rows]


@router.post("/me/notifications/read", status_code=204)
def mark_all_read(user: Actor, db: DB):
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read.is_(False))
        .values(read=True)
    )
    db.commit()


@router.put("/me/notifications/{notification_id}/read", status_code=204)
def mark_read(notification_id: int, user: Actor, db: DB):
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(404, "Notification not found.")
    n.read = True
    db.commit()


def partner_ids(db: Session, user: User) -> set[int]:
    rows = db.execute(
        select(Message.sender_id, Message.recipient_id).where(
            or_(Message.sender_id == user.id, Message.recipient_id == user.id)
        )
    )
    return {b if a == user.id else a for a, b in rows}


@router.get("/messages/conversations")
def conversations(user: Actor, db: DB):
    """People you can message: past correspondents plus maintainers/admins."""
    from app.store import AccountRole

    staff = set(
        db.scalars(select(AccountRole.user_id).where(AccountRole.role.in_(STAFF)))
    )
    ids = (partner_ids(db, user) | staff) - {user.id}
    out = []
    for other in db.scalars(select(User).where(User.id.in_(ids))) if ids else []:
        last = db.scalar(
            select(Message)
            .where(
                or_(
                    (Message.sender_id == user.id) & (Message.recipient_id == other.id),
                    (Message.sender_id == other.id) & (Message.recipient_id == user.id),
                )
            )
            .order_by(Message.id.desc())
            .limit(1)
        )
        out.append(
            {
                "user_id": other.id,
                "name": display_name(other),
                "staff": other.id in staff,
                "unread": db.scalar(
                    select(func.count())
                    .select_from(Message)
                    .where(
                        Message.sender_id == other.id,
                        Message.recipient_id == user.id,
                        Message.read.is_(False),
                    )
                ),
                "last": last.body[:120] if last else "",
                "last_at": last.created_at if last else 0,
            }
        )
    out.sort(key=lambda c: (c["last_at"], c["name"].lower()), reverse=True)
    return out


@router.get("/messages/{other_id}")
def thread(other_id: int, user: Actor, db: DB):
    other = db.get(User, other_id)
    if not other or other.id == user.id:
        raise HTTPException(404, "Conversation not found.")
    if other.id not in partner_ids(db, user) and not STAFF & (
        set(roles(db, user)) | set(roles(db, other))
    ):
        raise HTTPException(403, "This conversation is not available.")
    db.execute(
        update(Message)
        .where(
            Message.sender_id == other_id,
            Message.recipient_id == user.id,
            Message.read.is_(False),
        )
        .values(read=True)
    )
    db.commit()
    rows = db.scalars(
        select(Message)
        .where(
            or_(
                (Message.sender_id == user.id) & (Message.recipient_id == other_id),
                (Message.sender_id == other_id) & (Message.recipient_id == user.id),
            )
        )
        .order_by(Message.id)
    )
    return {
        "user": {"user_id": other.id, "name": display_name(other)},
        "messages": [message_view(m, user.id) for m in rows],
    }


class MessageInput(BaseModel):
    recipient_id: int
    body: str = Field(min_length=1, max_length=2000)

    @field_validator("body")
    @classmethod
    def not_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Write a message before sending")
        return value


@router.post("/messages", status_code=201)
def send_message(body: MessageInput, user: Actor, db: DB):
    recipient = db.get(User, body.recipient_id)
    if not recipient or recipient.id == user.id:
        raise HTTPException(404, "Recipient not found.")
    # Prevents unsolicited volunteer-to-volunteer messages: reply, or write to staff.
    allowed = (
        bool(STAFF & set(roles(db, user)))
        or bool(STAFF & set(roles(db, recipient)))
        or recipient.id in partner_ids(db, user)
    )
    if not allowed:
        raise HTTPException(
            403,
            "You can message maintainers, administrators, or people who wrote to you.",
        )
    message = Message(sender_id=user.id, recipient_id=recipient.id, body=body.body)
    db.add(message)
    db.commit()
    return message_view(message, user.id)
