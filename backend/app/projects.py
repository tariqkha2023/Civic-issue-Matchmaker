"""Configured civic projects; repository scope does not imply partnership."""

import re

from fastapi import HTTPException
from sqlalchemy import select

from app.store import Repository, SourceSettings

PROJECTS = [
    (
        "mysociety/fixmystreet",
        "FixMyStreet",
        "Public infrastructure",
        "Helps residents report street problems to the appropriate authorities.",
        ["perl", "javascript"],
    ),
    (
        "hotosm/tasking-manager",
        "HOT Tasking Manager",
        "Humanitarian mapping",
        "Coordinates collaborative mapping for humanitarian and community projects.",
        ["python", "react"],
    ),
    (
        "openstreetmap/iD",
        "OpenStreetMap iD",
        "Open mapping",
        "An editor for community-maintained geographic data.",
        ["javascript"],
    ),
    (
        "openfoodfacts/openfoodfacts-server",
        "Open Food Facts",
        "Food transparency",
        "Open information about food ingredients, nutrition, and environmental attributes.",
        ["perl", "javascript"],
    ),
    (
        "hackforla/website",
        "Hack for LA",
        "Civic participation",
        "Connects people with civic technology projects and community participation.",
        ["javascript", "html", "css"],
    ),
]


def validate_path(path):
    if not re.fullmatch(
        r"[A-Za-z0-9_-][A-Za-z0-9_.-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*", path
    ) or any(p in {".", ".."} for p in path.split("/")):
        raise HTTPException(422, "Use a GitHub owner/repository path, not a URL.")
    return path


def settings(db, repo):
    row = db.get(SourceSettings, repo.id)
    return {
        "interval_minutes": 60,
        "topics": [],
        "languages": [],
        "name": repo.path,
        "mission": "",
        "github_url": "https://github.com/" + repo.path,
        "contributing_url": "https://github.com/"
        + repo.path
        + "/blob/HEAD/CONTRIBUTING.md",
        "conduct_url": "https://github.com/"
        + repo.path
        + "/blob/HEAD/CODE_OF_CONDUCT.md",
        "complete": False,
        **(row.fields if row else {}),
    }


def configure_sources(db):
    for path, name, topic, mission, languages in PROJECTS:
        repo = db.scalar(
            select(Repository).where(
                Repository.source == "github", Repository.path == path
            )
        )
        if not repo:
            repo = Repository(source="github", path=path)
            db.add(repo)
            db.flush()
        if not db.get(SourceSettings, repo.id):
            db.add(
                SourceSettings(
                    repository_id=repo.id,
                    fields={
                        "name": name,
                        "topics": [topic.lower()],
                        "mission": mission,
                        "languages": languages,
                        "interval_minutes": 60,
                        "complete": False,
                    },
                )
            )
    db.commit()


def project_view(db, repo):
    from sqlalchemy import func

    from app.store import Task

    data = settings(db, repo)
    counts = dict(
        db.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.repository_id == repo.id)
            .group_by(Task.status)
        ).all()
    )
    return {
        **data,
        "id": repo.id,
        "path": repo.path,
        "source": repo.source,
        "enabled": repo.enabled,
        "last_successful_scan": repo.last_success,
        "error": repo.scan_error,
        "open_count": counts.get("open", 0),
        "closed_count": counts.get("closed", 0),
    }
