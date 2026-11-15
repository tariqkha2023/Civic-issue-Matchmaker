"""Discovery domain service: eligibility, filters and explained ranking."""

import os

from sqlalchemy import select

from app.discovery_context import reviewed_context
from app.discovery_search import search_result, skill_matches
from app.enrichment import effective_metadata, project_context
from app.store import Repository, SavedTask, Task
from app.views import projection_context, task_view


def search_match(task, meta, terms):
    result = search_result(task, meta, " ".join(terms))
    return result["kind"] if result else None


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
    include_suggested=True,
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
    # Context and synonym matches may exist only outside the source SQL columns.
    # Apply the complete search once, against validated effective metadata below.
    terms = q.split()
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
        match = search_result(
            task,
            meta,
            q,
            include_suggested,
            reviewed_context(task),
            context["projects"].get(repo.id, {}),
        )
        if terms and match is None:
            continue
        if topic and topic.lower() not in [t.lower() for t in meta["topics"]]:
            continue
        searchable_skills = [
            s
            for s in meta["skills"]
            if include_suggested or meta.get("skill_weights", {}).get(s, 1) >= 1
        ]
        if skill and not any(skill_matches(s, skill) for s in searchable_skills):
            continue
        if difficulty and difficulty != meta["difficulty"]:
            continue
        if max_effort is not None and (
            meta["effort"] is None or meta["effort"] > max_effort
        ):
            continue
        view = task_view(task, repo, task.id in saved, user.profile, db, user, context)
        if terms:
            view["search_match"] = match["kind"]
            view["search_related_wording"] = match["related_wording"]
        view["search_rank"] = match["rank"] if match else 0
        results.append(view)
    levels = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}
    keys = {
        "relevance": lambda t: (t["search_rank"], -t["first_seen"], t["id"]),
        "compatibility": lambda t: (
            -(t["score"] if t["score"] is not None else -1),
            -t["coverage"],
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
        or not user.profile.get("interests"),
    }
