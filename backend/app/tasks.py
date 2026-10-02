"""Task creation domain operations for local civic sources."""

import secrets

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.demo import get_demo_repository
from app.store import Repository, Task


def create_demo_issue(db, user, body):
    repo = get_demo_repository(db)
    if not repo.enabled:
        raise HTTPException(
            409, "The demo repository is disabled. Ask an administrator to enable it."
        )
    task = Task(
        repository_id=repo.id,
        source_id=secrets.token_hex(16),
        title=body.title,
        description=body.description,
        url="",
        status="open",
        labels=[body.topic] if body.topic else [],
        metadata_fields={
            "skills": body.skills,
            "topics": [body.topic] if body.topic else [],
            "difficulty": body.difficulty,
            "effort": body.effort,
            "location": body.location,
            "organizer": body.organizer,
            "created_by": user.id,
            "demo_sample": False,
            "provenance": "Created in the app and stored in the local demo repository.",
        },
    )
    db.add(task)
    db.commit()
    return task, repo


def create_manual_task(db, user, body):
    project = body.project.lower()
    repo = db.scalar(
        select(Repository).where(
            Repository.source == "manual", Repository.path == project
        )
    )
    if not repo:
        repo = Repository(source="manual", path=project)
        db.add(repo)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            repo = db.scalar(
                select(Repository).where(
                    Repository.source == "manual", Repository.path == project
                )
            )
    task = Task(
        repository_id=repo.id,
        source_id=secrets.token_hex(16),
        title=body.title,
        description=body.description,
        url=body.url,
        status="open",
        labels=[],
        metadata_fields={
            "skills": body.skills,
            "topics": [body.topic] if body.topic else [],
            "difficulty": body.difficulty,
            "effort": body.effort,
            "provenance": "Manually added by a signed-in user for temporary task discovery.",
            "created_by": user.id,
        },
    )
    db.add(task)
    db.commit()
    return task, repo
