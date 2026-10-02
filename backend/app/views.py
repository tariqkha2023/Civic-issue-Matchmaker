"""Task response projection using effective, source-preserving metadata."""

from app.matching import score
from app.services import can_maintain, effective_metadata, participation


def task_view(task, repo, saved=False, profile=None, db=None, user=None):
    metadata = effective_metadata(db, task) if db is not None else task.metadata_fields
    data = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "url": task.url,
        "status": task.status,
        "repository": repo.path,
        "source": repo.source,
        "labels": task.labels,
        "metadata": metadata,
        "first_seen": task.first_seen,
        "last_successful_scan": repo.last_success,
        "source_error": repo.scan_error,
        "saved": saved,
    }
    if profile is not None:
        data["score"], data["explanations"] = score(profile, metadata, repo.path)
    if db is not None and user is not None:
        data["participation"] = participation(db, user, task)
        data["can_manage"] = can_maintain(db, user, task.repository_id)
    return data
