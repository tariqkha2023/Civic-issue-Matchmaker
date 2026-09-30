"""Discovery domain service: eligibility, filters and explained ranking."""

from sqlalchemy import select

from app.services import effective_metadata
from app.store import Repository, SavedTask, Task
from app.views import task_view


def discover(
    db,
    user,
    q,
    repository,
    topic,
    skill,
    difficulty,
    max_effort,
    status,
    sort,
    page,
    page_size,
):
    saved = set(
        db.scalars(select(SavedTask.task_id).where(SavedTask.user_id == user.id))
    )
    statement = (
        select(Task, Repository).join(Repository).where(Repository.enabled.is_(True))
    )
    if status != "all":
        statement = statement.where(Task.status == status)
    if repository:
        statement = statement.where(Repository.path == repository)
    results = []
    for task, repo in db.execute(statement):
        if repo.selection_labels and not set(repo.selection_labels) & set(task.labels):
            continue
        meta = effective_metadata(db, task)
        if (
            q
            and q.lower()
            not in (
                task.title
                + " "
                + task.description
                + " "
                + " ".join(task.labels + meta["skills"] + meta["topics"])
            ).lower()
        ):
            continue
        if topic and topic.lower() not in [t.lower() for t in meta["topics"]]:
            continue
        if skill and skill.lower() not in meta["skills"]:
            continue
        if difficulty and difficulty != meta["difficulty"]:
            continue
        if max_effort is not None and (
            meta["effort"] is None or meta["effort"] > max_effort
        ):
            continue
        results.append(task_view(task, repo, task.id in saved, user.profile, db, user))
    levels = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}
    keys = {
        "compatibility": lambda t: (
            -(t["score"] if t["score"] is not None else -1),
            t["id"],
        ),
        "recency": lambda t: (-t["first_seen"], t["id"]),
        "difficulty": lambda t: (levels.get(t["metadata"]["difficulty"], 3), t["id"]),
        "effort": lambda t: (
            t["metadata"]["effort"]
            if t["metadata"]["effort"] is not None
            else float("inf"),
            t["id"],
        ),
    }
    results.sort(key=keys[sort])
    return {
        "items": results[(page - 1) * page_size : page * page_size],
        "total": len(results),
        "page": page,
        "profile_incomplete": not user.profile.get("skills")
        or not user.profile.get("interests")
        or not user.profile.get("hours"),
    }
