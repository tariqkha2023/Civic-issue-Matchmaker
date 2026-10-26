"""Discovery domain service: eligibility, filters and explained ranking."""

import os

from sqlalchemy import String, cast, or_, select

from app.enrichment import effective_metadata, project_context
from app.store import IssueEnrichment, MetadataCorrection, Repository, SavedTask, Task
from app.views import projection_context, task_view


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
    assignment="",
):
    saved = set(
        db.scalars(select(SavedTask.task_id).where(SavedTask.user_id == user.id))
    )
    statement = (
        select(Task, Repository).join(Repository).where(Repository.enabled.is_(True))
    )
    if os.getenv("APP_DEMO", "false").lower() != "true":
        statement = statement.where(Repository.source == "github")
    if status != "all":
        statement = statement.where(Task.status == status)
    if repository:
        statement = statement.where(Repository.path == repository)
    if q:
        pattern = (
            "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        )
        statement = statement.where(
            or_(
                Task.title.ilike(pattern, escape="\\"),
                Task.description.ilike(pattern, escape="\\"),
                cast(Task.labels, String).ilike(pattern, escape="\\"),
                cast(Task.metadata_fields, String).ilike(pattern, escape="\\"),
                Task.id.in_(
                    select(IssueEnrichment.task_id).where(
                        cast(IssueEnrichment.fields, String).ilike(pattern, escape="\\")
                    )
                ),
                Task.id.in_(
                    select(MetadataCorrection.task_id).where(
                        cast(MetadataCorrection.fields, String).ilike(
                            pattern, escape="\\"
                        )
                    )
                ),
            )
        )
    candidates = list(db.execute(statement))
    context = projection_context(db, user, [t.id for t, _ in candidates])
    results = []
    for task, repo in candidates:
        if (
            repo.source != "github"
            and repo.selection_labels
            and not set(repo.selection_labels) & set(task.labels)
        ):
            continue
        info = context["info"].get(task.id, {})
        if info.get("available") is False:
            continue
        if assignment and bool(info.get("assignees")) != (assignment == "assigned"):
            continue
        meta = effective_metadata(
            task,
            context["enrichments"].get(task.id),
            context["corrections"].get(task.id, {}),
            project_context(context["projects"][repo.id])
            if repo.id in context["projects"]
            else {},
        )
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
        results.append(
            task_view(task, repo, task.id in saved, user.profile, db, user, context)
        )
    levels = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}
    keys = {
        "compatibility": lambda t: (
            -(t["score"] if t["score"] is not None else -1),
            int(t["feedback"] is not None and not t["feedback"]["relevant"]),
            -int(t["id"] in context["completed"]),
            -int(t["repository"].lower() in user.profile.get("repositories", [])),
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
