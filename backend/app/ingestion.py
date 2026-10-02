"""Atomic scans preserve the previous snapshot on any source failure."""

import time
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.connectors.github import GitHubConnector
from app.connectors.gitlab import GitLabConnector
from app.matching import derive_metadata
from app.store import Repository, Task


class ImportedTask(BaseModel):
    source_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=1000)
    description: str = Field(max_length=1000000)
    url: str = Field(max_length=2000)
    status: str
    labels: list[str] = Field(max_length=200)


def scan_repository(db, repository, token=None):
    connector = (
        GitHubConnector(*repository.path.split("/"), token=token)
        if repository.source == "github"
        else GitLabConnector(repository.path, token=token)
    )
    repo_id = repository.id
    try:
        tasks = connector.fetch_tasks()
        seen = set()
        eligible = set()
        for imported in tasks:
            imported = ImportedTask(
                **{
                    field: getattr(imported, field)
                    for field in ImportedTask.model_fields
                }
            )
            parsed = urlparse(imported.url)
            allowed_host = (
                "github.com" if repository.source == "github" else "gitlab.com"
            )
            if parsed.scheme != "https" or parsed.hostname != allowed_host:
                raise ValueError("Invalid authoritative source URL")
            if not imported.title or imported.status not in {"open", "opened"}:
                raise ValueError("Invalid task data")
            seen.add(imported.source_id)
            selected = not repository.selection_labels or bool(
                set(repository.selection_labels) & set(imported.labels)
            )
            if selected:
                eligible.add(imported.source_id)
            task = db.scalar(
                select(Task).where(
                    Task.repository_id == repo_id, Task.source_id == imported.source_id
                )
            )
            if task is None:
                if not selected:
                    continue
                task = Task(repository_id=repo_id, source_id=imported.source_id)
                db.add(task)
            task.title = imported.title
            task.description = imported.description
            task.url = imported.url
            task.status = "open"
            task.labels = imported.labels
            task.metadata_fields = derive_metadata(imported.labels)
        for task in db.scalars(select(Task).where(Task.repository_id == repo_id)):
            if task.source_id not in seen:
                task.status = "closed"
        repository.last_success = time.time()
        repository.scan_error = None
        db.commit()
        return len(eligible)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        db.rollback()
        repository = db.get(Repository, repo_id)
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            message = {
                401: "Source authorization failed.",
                403: "Source access denied or rate limited.",
                429: "Source rate limited.",
            }.get(status, "Source request failed.")
        elif isinstance(exc, httpx.HTTPError):
            message = "Source unavailable. Cached tasks have been preserved."
        else:
            message = "Malformed source data. Cached tasks have been preserved."
        repository.scan_error = message
        db.commit()
        raise RuntimeError(message) from None
