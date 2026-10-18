"""Read-only, resumable GitHub tracker synchronization.

Pages are staged until a complete scan succeeds. Published source snapshots are
never partially overwritten. Anonymous API limits pause rather than lose progress.
"""

import os
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

import httpx
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from app.matching import derive_metadata, score
from app.projects import settings, validate_path
from app.store import (
    IssueInfo,
    JobLease,
    MetadataCorrection,
    Repository,
    ScanRun,
    SourceSettings,
    StagedIssue,
    Task,
    User,
)

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}


class SourceFailure(Exception):
    def __init__(self, message, retry_at=None):
        self.retry_at = retry_at or time.time() + 300
        super().__init__(message)


def read(client, url, token=None, redirects=0):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "api.github.com" or parsed.username:
        raise SourceFailure("Unsafe source URL rejected.")
    for attempt in range(3):
        try:
            response = client.get(
                url,
                headers={
                    **HEADERS,
                    **({"Authorization": f"Bearer {token}"} if token else {}),
                },
            )
        except httpx.HTTPError:
            if attempt == 2:
                raise SourceFailure(
                    "GitHub unavailable. Previous snapshot preserved."
                ) from None
            time.sleep(2**attempt)
            continue
        if response.status_code in {301, 302, 307, 308}:
            if redirects >= 3 or not response.headers.get("location"):
                raise SourceFailure("GitHub redirect limit exceeded.")
            destination = urljoin(url, response.headers["location"])
            return read(client, destination, token, redirects + 1)
        if response.status_code in {403, 429}:
            reset = response.headers.get("x-ratelimit-reset", "")
            retry = response.headers.get("retry-after", "")
            retry_at = max(
                time.time() + 60,
                float(reset)
                if reset.isdigit()
                else time.time() + int(retry)
                if retry.isdigit()
                else time.time() + 3600,
            )
            raise SourceFailure(
                "GitHub access denied or rate limited. Scan will resume; public-read token increases quota.",
                retry_at,
            )
        if response.status_code >= 500 and attempt < 2:
            time.sleep(2**attempt)
            continue
        if response.status_code != 200:
            raise SourceFailure(
                f"GitHub returned HTTP {response.status_code}. Previous snapshot preserved."
            )
        return response
    raise SourceFailure("GitHub unavailable.")


def acquire(db, name, seconds=900):
    row = db.get(JobLease, name)
    if not row:
        try:
            with db.begin_nested():
                db.add(JobLease(name=name))
                db.flush()
        except IntegrityError:
            pass
    now = time.time()
    won = db.execute(
        update(JobLease)
        .where(JobLease.name == name, JobLease.expires_at < now)
        .values(expires_at=now + seconds)
    )
    db.commit()
    return won.rowcount == 1


def release(db, name):
    db.execute(update(JobLease).where(JobLease.name == name).values(expires_at=0))
    db.commit()


def save_checkpoint(db, row, config):
    latest = (
        db.scalar(
            select(SourceSettings.fields).where(
                SourceSettings.repository_id == row.repository_id
            )
        )
        or {}
    )
    # Scanning owns progress; administrators own project descriptions and schedules.
    for key in ["name", "mission", "topics", "languages", "interval_minutes"]:
        if key in latest:
            config[key] = latest[key]
    row.fields = dict(config)


def sync_source(db, repo, max_pages=5, transport=None):
    if repo.source != "github" or not repo.enabled:
        return "disabled"
    lock = f"source:{repo.id}"
    if not acquire(db, lock):
        return "running"
    run = ScanRun(repository_id=repo.id, status="running")
    db.add(run)
    db.commit()
    try:
        row = db.get(SourceSettings, repo.id)
        if not row:
            row = SourceSettings(repository_id=repo.id, fields={})
            db.add(row)
            db.flush()
        config = settings(db, repo)
        path = validate_path(repo.path)
        with httpx.Client(
            timeout=20, follow_redirects=False, transport=transport
        ) as client:
            if not config.get("cursor"):
                response = read(
                    client,
                    "https://api.github.com/repos/" + path,
                    os.getenv("GITHUB_TOKEN"),
                )
                project = response.json()
                if not isinstance(project, dict) or not isinstance(
                    project.get("id"), int
                ):
                    raise ValueError("Missing repository identity")
                if project.get("private") or project.get("visibility") == "private":
                    raise SourceFailure(
                        "Only public civic repositories may be published to contributors."
                    )
                canonical = validate_path(project["full_name"])
                if project.get("html_url") != f"https://github.com/{canonical}":
                    raise SourceFailure("Invalid canonical GitHub repository URL.")
                if config.get("github_id") and config["github_id"] != project["id"]:
                    raise SourceFailure(
                        "Repository identity changed. Administrator review required."
                    )
                collision = db.scalar(
                    select(Repository.id).where(
                        Repository.source == "github",
                        Repository.path == canonical,
                        Repository.id != repo.id,
                    )
                )
                if collision:
                    raise SourceFailure(
                        "Renamed repository is already configured; administrator reconciliation required."
                    )
                repo.path = canonical
                config.update(
                    github_id=project["id"],
                    github_url=project["html_url"],
                    description=project.get("description") or "",
                    scan_started=time.time(),
                    staged_count=0,
                    pages=0,
                )
                full = (
                    not config.get("complete")
                    or config.pop("force_full", False)
                    or time.time() - config.get("last_full", 0) > 604800
                )
                config["full_scan"] = full
                config["cursor"] = (
                    f"https://api.github.com/repos/{canonical}/issues?state=all&per_page=100&sort=created&direction=asc"
                )
                if not full and repo.last_success:
                    since = (
                        datetime.fromtimestamp(repo.last_success - 60, timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z")
                    )
                    config["cursor"] += "&since=" + since
                db.execute(
                    delete(StagedIssue).where(StagedIssue.repository_id == repo.id)
                )
                save_checkpoint(db, row, config)
                db.commit()
            expected_paths = {
                f"/repos/{repo.path}/issues",
                f"/repositories/{config['github_id']}/issues",
            }
            for _ in range(max_pages):
                url = config["cursor"]
                if urlsplit(url).path not in expected_paths:
                    raise SourceFailure("Unsafe pagination destination rejected.")
                response = read(client, url, os.getenv("GITHUB_TOKEN"))
                payload = response.json()
                if not isinstance(payload, list):
                    raise ValueError("Malformed issue page")
                for raw in payload:
                    if not isinstance(raw, dict):
                        raise ValueError("Malformed issue")
                    if "pull_request" in raw:
                        continue
                    if (
                        not isinstance(raw.get("id"), int)
                        or not isinstance(raw.get("number"), int)
                        or raw.get("state") not in {"open", "closed"}
                        or not isinstance(raw.get("title"), str)
                        or not raw["title"].strip()
                    ):
                        raise ValueError("Missing issue fields")
                    if (
                        raw.get("html_url")
                        != f"https://github.com/{repo.path}/issues/{raw['number']}"
                    ):
                        raise ValueError("Invalid authoritative issue URL")
                    source_id = str(raw["id"])
                    fields = {
                        "title": raw["title"],
                        "description": raw.get("body") or "",
                        "url": raw["html_url"],
                        "status": raw["state"],
                        "labels": [label["name"] for label in raw.get("labels", [])],
                        "number": raw["number"],
                        "assignees": [a["login"] for a in raw.get("assignees", [])],
                        "author": (raw.get("user") or {}).get("login"),
                        "created_at": raw.get("created_at"),
                        "updated_at": raw.get("updated_at"),
                        "closed_at": raw.get("closed_at"),
                    }
                    stage = db.get(StagedIssue, (repo.id, source_id))
                    if stage:
                        stage.fields = fields
                    else:
                        db.add(
                            StagedIssue(
                                repository_id=repo.id,
                                source_id=source_id,
                                fields=fields,
                            )
                        )
                    config["staged_count"] = config.get("staged_count", 0) + 1
                nxt = response.links.get("next", {}).get("url")
                if nxt and (nxt == url or config.get("pages", 0) >= 10000):
                    raise SourceFailure("Pagination loop or scan limit exceeded.")
                repo.scan_error = None
                config["pages"] = config.get("pages", 0) + 1
                config["cursor"] = nxt
                config["next_due"] = time.time() + 15
                save_checkpoint(db, row, config)
                db.commit()
                if not nxt:
                    publish(db, repo, row, config)
                    run.status, run.count = "completed", config["staged_count"]
                    break
            else:
                run.status, run.count = "paused", config["staged_count"]
                run.detail = "Staging tracker pages; previous complete snapshot remains published."
    except (SourceFailure, httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        db.rollback()
        repo = db.get(Repository, repo.id)
        row = db.get(SourceSettings, repo.id)
        config = dict(row.fields) if row else {}
        config["next_due"] = (
            exc.retry_at if isinstance(exc, SourceFailure) else time.time() + 300
        )
        if row:
            row.fields = config
        repo.scan_error = (
            str(exc)
            if isinstance(exc, SourceFailure)
            else "Malformed GitHub data. Previous complete snapshot preserved."
        )
        run = db.get(ScanRun, run.id)
        run.status, run.detail = "failed", repo.scan_error
    finally:
        run.finished_at = time.time()
        db.commit()
        release(db, lock)
    return run.status


def publish(db, repo, row, config):
    from app.events import deliver
    from app.store import AccountSettings

    stages = list(
        db.scalars(select(StagedIssue).where(StagedIssue.repository_id == repo.id))
    )
    existing = {
        task.source_id: task
        for task in db.scalars(select(Task).where(Task.repository_id == repo.id))
    }
    info_map = {
        info.task_id: info
        for info in db.scalars(
            select(IssueInfo).join(Task).where(Task.repository_id == repo.id)
        )
    }
    corrections = {
        c.task_id: c
        for c in db.scalars(
            select(MetadataCorrection).join(Task).where(Task.repository_id == repo.id)
        )
    }
    users = [u for u in db.scalars(select(User)) if not u.profile.get("deleted")]
    pref_rows = {p.user_id: p.preferences for p in db.scalars(select(AccountSettings))}
    matches = {u.id: [] for u in users}
    match_counts = {u.id: 0 for u in users}
    prepared = []
    seen = set()
    for stage in stages:
        data = stage.fields
        seen.add(stage.source_id)
        task = existing.get(stage.source_id)
        fresh = task is None
        reopened = not fresh and task.status == "closed" and data["status"] == "open"
        changed = not fresh and (
            task.title != data["title"]
            or task.description != data["description"]
            or task.labels != data["labels"]
        )
        if fresh:
            task = Task(repository_id=repo.id, source_id=stage.source_id)
            db.add(task)
        for key in ["title", "description", "url", "status", "labels"]:
            setattr(task, key, data[key])
        meta = derive_metadata(data["labels"])
        if not meta["topics"]:
            meta["topics"] = config.get("topics", [])
        meta["project_languages"] = config.get("languages", [])
        meta["provenance"] = (
            "Issue labels and curated project topic; project languages are context, not required skills."
        )
        task.metadata_fields = meta
        prepared.append((task, data, fresh or changed or reopened, changed))
    db.flush()
    for task, data, notify_match, changed in prepared:
        info = info_map.get(task.id)
        if not info:
            info = IssueInfo(task_id=task.id)
            db.add(info)
        info.fields = {
            key: data[key]
            for key in [
                "number",
                "assignees",
                "author",
                "created_at",
                "updated_at",
                "closed_at",
            ]
        } | {"available": True}
        correction = corrections.get(task.id)
        if changed and correction:
            correction.fields = {**correction.fields, "needs_review": True}
        if notify_match and task.status == "open":
            effective = {
                **task.metadata_fields,
                **(correction.fields if correction else {}),
            }
            for user in users:
                pref = pref_rows.get(user.id, {})
                if not pref.get("new_matches", True):
                    continue
                result, _ = score(user.profile, effective, repo.path)
                if result is not None and result >= pref.get("minimum_score", 60):
                    match_counts[user.id] += 1
                    if len(matches[user.id]) < 5:
                        matches[user.id].append(task.title)
    # One digest per user/scan avoids a notification storm on initial indexing.
    for user in users:
        count = match_counts[user.id]
        if count:
            deliver(
                db,
                user.id,
                f"scan-matches:{repo.id}:{config['scan_started']}",
                f"{count} new or updated matches in {repo.path}",
                "; ".join(matches[user.id]) + ". Open Projects to browse all matches.",
                "new_matches",
            )
    if config["full_scan"]:
        for sid, task in existing.items():
            if sid not in seen and task.id in info_map:
                info_map[task.id].fields = {
                    **info_map[task.id].fields,
                    "available": False,
                }
        config["last_full"] = time.time()
    repo.last_success = config["scan_started"]
    repo.scan_error = None
    config.update(
        complete=True,
        next_due=time.time() + config.get("interval_minutes", 60) * 60,
        cursor=None,
        staged_count=len(stages),
    )
    save_checkpoint(db, row, config)
    db.execute(delete(StagedIssue).where(StagedIssue.repository_id == repo.id))
    db.commit()
