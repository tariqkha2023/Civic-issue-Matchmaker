"""Private, nonexclusive contribution activity and bounded relevance feedback."""

import re
import time
from typing import Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from app.application import DB, Actor
from app.store import (
    Contribution,
    IssueInfo,
    RelevanceFeedback,
    Repository,
    Task,
)

router = APIRouter(prefix="/api")


class ActivityInput(BaseModel):
    state: Literal["interested", "in_progress", "submitted", "completed", "withdrawn"]
    evidence: str = Field(default="", max_length=2000)
    note: str = Field(default="", max_length=1000)
    expected_version: float | None = None

    @field_validator("evidence")
    @classmethod
    def github_link(cls, value):
        value = value.strip()
        if value:
            url = urlsplit(value)
            if (
                url.scheme != "https"
                or url.netloc != "github.com"
                or not re.fullmatch(r"/[\w.-]+/[\w.-]+/(pull|issues)/\d+", url.path)
                or url.query
                or url.fragment
            ):
                raise ValueError(
                    "Use an https://github.com/owner/repo/pull/123 or /issues/123 link"
                )
        return value


def activity_view(db, item):
    task = db.get(Task, item.task_id)
    repo = db.get(Repository, task.repository_id)
    return {
        "id": item.id,
        "task_id": item.task_id,
        "title": task.title,
        "url": task.url,
        "repository": repo.path,
        "source_enabled": repo.enabled,
        "source_state": task.status,
        "state": item.state,
        "evidence": item.evidence,
        "note": item.note,
        "updated_at": item.updated_at,
        "events": item.events,
        "completion_basis": "Self-reported; no upstream acceptance verified"
        if item.state == "completed"
        else "Local tracking only",
    }


@router.get("/me/contributions")
def activities(user: Actor, db: DB):
    rows = db.scalars(
        select(Contribution)
        .where(Contribution.user_id == user.id)
        .order_by(Contribution.updated_at.desc())
    )
    return [activity_view(db, item) for item in rows]


@router.post("/tasks/{task_id}/contributions", status_code=201)
def start_tracking(task_id: int, user: Actor, db: DB):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Issue not found.")
    repo = db.get(Repository, task.repository_id)
    info = db.get(IssueInfo, task.id)
    if (
        not repo.enabled
        or task.status != "open"
        or (info and info.fields.get("available") is False)
    ):
        raise HTTPException(
            409, "Start new tracking on an open issue from an enabled source."
        )
    existing = db.scalar(
        select(Contribution).where(
            Contribution.user_id == user.id,
            Contribution.task_id == task_id,
            Contribution.state.in_(["interested", "in_progress", "submitted"]),
        )
    )
    if existing:
        return activity_view(db, existing)
    now = time.time()
    row = Contribution(
        user_id=user.id,
        task_id=task_id,
        state="interested",
        updated_at=now,
        events=[
            {
                "state": "interested",
                "time": now,
                "basis": "Local intent; not GitHub assignment",
            }
        ],
    )
    db.add(row)
    from app.events import deliver

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        row = db.scalar(
            select(Contribution).where(
                Contribution.user_id == user.id,
                Contribution.task_id == task_id,
                Contribution.state.in_(["interested", "in_progress", "submitted"]),
            )
        )
        if not row:
            raise HTTPException(409, "Tracking changed. Refresh and retry.") from None
        return activity_view(db, row)
    deliver(
        db,
        user.id,
        f"track:{task_id}:{now}",
        "Contribution tracked",
        task.title,
        "activity",
    )
    db.commit()
    return activity_view(db, row)


@router.put("/me/contributions/{activity_id}")
def update_activity(activity_id: int, body: ActivityInput, user: Actor, db: DB):
    row = db.scalar(
        select(Contribution)
        .where(Contribution.id == activity_id, Contribution.user_id == user.id)
        .with_for_update()
    )
    if not row:
        raise HTTPException(404, "Contribution not found.")
    if body.expected_version is not None and body.expected_version != row.updated_at:
        raise HTTPException(409, "This contribution changed. Refresh before updating.")
    transitions = {
        "interested": {"interested", "in_progress", "withdrawn"},
        "in_progress": {"in_progress", "submitted", "completed", "withdrawn"},
        "submitted": {"submitted", "in_progress", "completed", "withdrawn"},
        "withdrawn": {"interested"},
        "completed": set(),
    }
    if body.state not in transitions[row.state]:
        raise HTTPException(
            409,
            "Invalid transition. Completed activity cannot be edited; remove it or start a new contribution for more work.",
        )
    evidence = body.evidence.strip()
    note = body.note.strip()
    if body.state == "submitted" and not evidence:
        raise HTTPException(
            422, "Add a GitHub submission link before marking submitted."
        )
    if body.state == "completed" and not note:
        raise HTTPException(
            422, "Describe your completed contribution. Completion is self-reported."
        )
    now = time.time()
    events = [
        *row.events,
        {
            "state": body.state,
            "time": now,
            "evidence": evidence,
            "note": note,
            "basis": "Self-reported",
        },
    ]
    changed = db.execute(
        update(Contribution)
        .where(Contribution.id == row.id, Contribution.updated_at == row.updated_at)
        .values(
            state=body.state,
            evidence=evidence,
            note=note,
            updated_at=now,
            events=events,
        )
    )
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Contribution changed. Refresh before updating.")
    db.refresh(row)
    from app.events import deliver

    deliver(
        db,
        user.id,
        f"activity:{row.id}:{row.updated_at}",
        "Contribution " + row.state.replace("_", " "),
        db.get(Task, row.task_id).title,
        "activity",
    )
    db.commit()
    return activity_view(db, row)


@router.delete("/me/contributions/{activity_id}", status_code=204)
def remove_activity(
    activity_id: int, user: Actor, db: DB, expected_version: float | None = None
):
    row = db.scalar(
        select(Contribution)
        .where(Contribution.id == activity_id, Contribution.user_id == user.id)
        .with_for_update()
    )
    if not row:
        raise HTTPException(404, "Contribution not found.")
    if expected_version is not None and expected_version != row.updated_at:
        raise HTTPException(
            409, "This contribution changed. Refresh before removing it."
        )
    removed = db.execute(
        delete(Contribution).where(
            Contribution.id == row.id,
            Contribution.user_id == user.id,
            Contribution.updated_at == row.updated_at,
        )
    )
    if removed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Contribution changed. Refresh before removing it.")
    db.commit()


class FeedbackInput(BaseModel):
    relevant: bool
    explanation: str = Field(default="", max_length=1000)


@router.put("/tasks/{task_id}/feedback")
def feedback(task_id: int, body: FeedbackInput, user: Actor, db: DB):
    if not db.get(Task, task_id):
        raise HTTPException(404, "Issue not found.")
    row = db.get(RelevanceFeedback, (user.id, task_id))
    if not row:
        row = RelevanceFeedback(user_id=user.id, task_id=task_id)
        db.add(row)
    row.relevant, row.explanation, row.updated_at = (
        body.relevant,
        body.explanation.strip(),
        time.time(),
    )
    db.commit()
    return {"relevant": row.relevant, "explanation": row.explanation}


@router.get("/me/feedback")
def feedback_history(user: Actor, db: DB):
    return [
        {
            "task_id": f.task_id,
            "title": db.get(Task, f.task_id).title,
            "relevant": f.relevant,
            "explanation": f.explanation,
            "updated_at": f.updated_at,
        }
        for f in db.scalars(
            select(RelevanceFeedback).where(RelevanceFeedback.user_id == user.id)
        )
    ]
