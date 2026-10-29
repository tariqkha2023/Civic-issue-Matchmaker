"""Public-only GitHub issue/cache handoff. No network requests or private-table export."""

import argparse
import gzip
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment import MODEL, VERSION, cached_fields, fingerprint, project_context
from app.enrichment_prompt import PROMPT_VERSION, SYSTEM_PROMPT
from app.migrations import migrate
from app.store import (
    IssueEnrichment,
    IssueInfo,
    Repository,
    SourceSettings,
    Task,
    engine,
)

DEFAULT_SNAPSHOT = Path(__file__).resolve().parents[2] / "data/public-issues-v1.json.gz"
MAX_BYTES = 256 * 1024 * 1024


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Project(PublicModel):
    # These four context fields must retain their exact values for cache hashes.
    name: str | None = None
    mission: str | None = None
    languages: list[str] | None = None
    topics: list[str] | None = None
    github_id: int = Field(gt=0)
    github_url: str
    description: str = ""
    contributing_url: str | None = None
    conduct_url: str | None = None
    interval_minutes: int = Field(default=60, ge=60, le=10080)
    complete: Literal[True] = True
    last_full: float = Field(default=0, ge=0)


class Metadata(PublicModel):
    skills: list[str]
    topics: list[str]
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] | None
    effort: float | None = Field(default=None, ge=0)
    provenance: str
    project_languages: list[str] = Field(default_factory=list)


class Upstream(PublicModel):
    number: int = Field(gt=0)
    assignees: list[str] = Field(default_factory=list)
    author: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    closed_at: str | None = None
    available: bool = True


class Evidence(PublicModel):
    skill: str
    quote: str | None = None
    basis: Literal["explicit", "inferred"] = "explicit"
    rationale: str | None = None


class CacheFields(PublicModel):
    status: Literal["accepted", "rejected"]
    skills: list[str]
    evidence: list[Evidence]
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] | None
    difficulty_evidence: str | None = None
    prompt_version: str | None = None


class Cache(PublicModel):
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    model: str
    fields: CacheFields
    cost: float = Field(ge=0)
    updated_at: float = Field(ge=0)


class Issue(PublicModel):
    source_id: str = Field(pattern=r"^[1-9][0-9]*$")
    title: str = Field(min_length=1)
    description: str
    url: str
    status: Literal["open", "closed"]
    labels: list[str]
    metadata_fields: Metadata
    first_seen: float = Field(ge=0)
    upstream: Upstream
    enrichment: Cache | None = None


class Source(PublicModel):
    path: str
    enabled: bool
    last_success: float = Field(ge=0)
    project: Project
    issues: list[Issue]

    @model_validator(mode="after")
    def check_identity(self):
        if not re.fullmatch(
            r"[A-Za-z0-9_-][A-Za-z0-9_.-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*", self.path
        ):
            raise ValueError("Invalid GitHub repository path")
        base = "https://github.com/" + self.path
        if self.project.github_url != base:
            raise ValueError("Invalid public repository URL")
        for url in [self.project.contributing_url, self.project.conduct_url]:
            if url is not None and not url.startswith(base + "/"):
                raise ValueError("Invalid project document URL")
        seen = set()
        for issue in self.issues:
            if issue.source_id in seen:
                raise ValueError("Duplicate upstream issue identifier")
            seen.add(issue.source_id)
            if issue.url != f"{base}/issues/{issue.upstream.number}":
                raise ValueError("Invalid authoritative issue URL")
            if issue.enrichment and (
                issue.enrichment.model != MODEL
                or issue.enrichment.content_hash
                != fingerprint(issue, project_context(self.project.model_dump()))
            ):
                raise ValueError("Cache does not match issue/project content")
        return self


class Snapshot(PublicModel):
    format: Literal["civic-public-issues"] = "civic-public-issues"
    schema_version: Literal[1] = 1
    created_at: str
    extraction_version: str
    model: str
    prompt_version: str
    system_prompt: str
    sources: list[Source]

    @model_validator(mode="after")
    def check_versions(self):
        if (self.extraction_version, self.model, self.prompt_version, self.system_prompt) != (
            VERSION, MODEL, PROMPT_VERSION, SYSTEM_PROMPT
        ):
            raise ValueError("Snapshot requires its matching extraction code/prompt version")
        ids = [source.project.github_id for source in self.sources]
        paths = [source.path.casefold() for source in self.sources]
        if len(set(ids)) != len(ids) or len(set(paths)) != len(paths):
            raise ValueError("Duplicate public repository identity")
        return self


class Envelope(PublicModel):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    data: Snapshot


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def public_fields(model, fields):
    """Project nested JSON through an explicit allowlist, never dump arbitrary fields."""
    return {key: fields[key] for key in model.model_fields if key in fields}


def export_snapshot(path=DEFAULT_SNAPSHOT, db_engine=engine):
    sources = []
    # This transaction only reads the public tables; it does not migrate the live DB.
    with Session(db_engine) as db:
        if db_engine.dialect.name == "sqlite":
            # SQLite's legacy driver otherwise does not start a read transaction
            # for SELECTs, so concurrent source publication could mix generations.
            db.connection().exec_driver_sql("BEGIN")
        for repo in db.scalars(select(Repository).where(Repository.source == "github").order_by(Repository.path)):
            row = db.get(SourceSettings, repo.id)
            if not row or not row.fields.get("complete") or not row.fields.get("github_id"):
                continue  # No unpublished staging data or unverified local fixtures.
            project = public_fields(Project, row.fields)
            context = project_context(project)
            infos = {r.task_id: r for r in db.scalars(select(IssueInfo).join(Task).where(Task.repository_id == repo.id))}
            caches = {r.task_id: r for r in db.scalars(select(IssueEnrichment).join(Task).where(Task.repository_id == repo.id))}
            issues = []
            for task in db.scalars(select(Task).where(Task.repository_id == repo.id).order_by(Task.source_id)):
                info = infos.get(task.id)
                if not info:
                    raise ValueError("Published GitHub issue is missing source provenance")
                issue = {key: getattr(task, key) for key in [
                    "source_id", "title", "description", "url", "status", "labels", "first_seen"
                ]}
                issue["metadata_fields"] = public_fields(Metadata, task.metadata_fields)
                issue["upstream"] = public_fields(Upstream, info.fields)
                cache = caches.get(task.id)
                if cached_fields(task, cache, context):
                    fields = public_fields(CacheFields, cache.fields)
                    fields["evidence"] = [public_fields(Evidence, item) for item in fields["evidence"]]
                    issue["enrichment"] = {
                        "content_hash": cache.content_hash, "model": cache.model,
                        "fields": fields, "cost": cache.cost, "updated_at": cache.updated_at,
                    }
                issues.append(issue)
            sources.append(dict(path=repo.path, enabled=repo.enabled, last_success=repo.last_success,
                                project=project, issues=issues))
    if not sources:
        raise ValueError("No complete public GitHub sources available to export")
    data = dict(created_at=datetime.now(timezone.utc).isoformat(), extraction_version=VERSION,
                model=MODEL, prompt_version=PROMPT_VERSION, system_prompt=SYSTEM_PROMPT, sources=sources)
    validated = Snapshot.model_validate(data).model_dump()
    digest = hashlib.sha256(canonical(validated)).hexdigest()
    packed = gzip.compress(canonical(dict(sha256=digest, data=validated)), mtime=0)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(packed)
    temporary.replace(path)
    manifest = {
        "schema_version": 1, "created_at": validated["created_at"], "payload_sha256": digest,
        "gzip_sha256": hashlib.sha256(packed).hexdigest(), "compressed_bytes": len(packed),
        "extraction_version": VERSION, "model": MODEL, "prompt_version": PROMPT_VERSION,
        "sources": [{"path": s["path"], "issues": len(s["issues"]),
                     "open_issues": sum(i["status"] == "open" for i in s["issues"]),
                     "cached_enrichments": sum(i["enrichment"] is not None for i in s["issues"])}
                    for s in validated["sources"]],
    }
    path.with_name(path.name.removesuffix(".json.gz") + ".manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def load_snapshot(path):
    with gzip.open(path, "rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Snapshot exceeds the 256 MiB uncompressed limit")
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != {"sha256", "data"} or hashlib.sha256(canonical(data["data"])).hexdigest() != data["sha256"]:
        raise ValueError("Snapshot checksum mismatch")
    return Envelope.model_validate(data).data


def import_snapshot(path=DEFAULT_SNAPSHOT, db_engine=engine):
    snapshot = load_snapshot(path)  # Validate completely before any DB writes.
    migrate(db_engine)
    result = dict(sources=0, created_issues=0, updated_issues=0, skipped_newer=0,
                  imported_caches=0, skipped_caches=0)
    with Session(db_engine) as db, db.begin():
        repos = list(db.scalars(select(Repository).where(Repository.source == "github")))
        settings = {r.repository_id: r for r in db.scalars(select(SourceSettings))}
        for source in snapshot.sources:
            by_id = [r for r in repos if settings.get(r.id) and settings[r.id].fields.get("github_id") == source.project.github_id]
            by_path = [r for r in repos if r.path.casefold() == source.path.casefold()]
            if len(by_id) > 1 or len(by_path) > 1 or (by_id and by_path and by_id[0].id != by_path[0].id):
                raise ValueError("Conflicting local repository identities; import rolled back")
            repo = (by_id or by_path or [None])[0]
            fresh = repo is None
            if fresh:
                repo = Repository(source="github", path=source.path, enabled=source.enabled,
                                  selection_labels=[])
                db.add(repo)
                db.flush()
                repos.append(repo)
            row = settings.get(repo.id)
            local = row.fields if row else {}
            if local.get("github_id") not in (None, source.project.github_id):
                raise ValueError("Repository path now belongs to another upstream identity")
            newer = bool(repo.last_success and repo.last_success > source.last_success)
            complete = bool(local.get("complete"))
            if not complete:
                if row is None:
                    row = SourceSettings(repository_id=repo.id)
                    db.add(row)
                    settings[repo.id] = row
                row.fields = {**source.project.model_dump(exclude_none=True),
                              **project_context(source.project.model_dump()), "cursor": None,
                              "next_due": time.time() + source.project.interval_minutes * 60}
            elif not local.get("github_id"):
                row.fields = {**local, "github_id": source.project.github_id}
            if not newer:
                repo.path = source.path
                repo.last_success = source.last_success
            context = project_context(row.fields)
            tasks = {t.source_id: t for t in db.scalars(select(Task).where(Task.repository_id == repo.id))}
            infos = {r.task_id: r for r in db.scalars(select(IssueInfo).join(Task).where(Task.repository_id == repo.id))}
            caches = {r.task_id: r for r in db.scalars(select(IssueEnrichment).join(Task).where(Task.repository_id == repo.id))}
            for issue in source.issues:
                task = tasks.get(issue.source_id)
                info = infos.get(task.id) if task else None
                later = bool(info and info.fields.get("updated_at") and
                             (info.fields["updated_at"] > (issue.upstream.updated_at or "")))
                if task is not None and (newer or later):
                    result["skipped_newer"] += 1
                else:
                    if task is None:
                        task = Task(repository_id=repo.id, source_id=issue.source_id,
                                    first_seen=issue.first_seen)
                        db.add(task)
                        result["created_issues"] += 1
                    else:
                        result["updated_issues"] += 1
                    for key in ["title", "description", "url", "status", "labels"]:
                        setattr(task, key, getattr(issue, key))
                    task.metadata_fields = issue.metadata_fields.model_dump()
                    db.flush()
                    if info is None:
                        info = IssueInfo(task_id=task.id)
                        db.add(info)
                    info.fields = issue.upstream.model_dump()
                cache = issue.enrichment
                if cache:
                    existing = caches.get(task.id)
                    if fingerprint(task, context) != cache.content_hash or (
                        existing and existing.updated_at > cache.updated_at
                    ):
                        result["skipped_caches"] += 1
                        continue
                    if existing is None:
                        existing = IssueEnrichment(task_id=task.id)
                        db.add(existing)
                    for key in ["content_hash", "model", "cost", "updated_at"]:
                        setattr(existing, key, getattr(cache, key))
                    existing.fields = cache.fields.model_dump()
                    result["imported_caches"] += 1
            result["sources"] += 1
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["export", "import", "setup"])
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()
    try:
        result = (export_snapshot if args.command == "export" else import_snapshot)(args.path)
    except (ValueError, OSError) as exc:
        # Do not print validation input values (which may include local private fields).
        parser.exit(1, f"Snapshot {args.command} failed ({type(exc).__name__}); no partial public import was committed.\n")
    print(json.dumps(result, indent=2))
    if args.command == "setup":
        from app.bootstrap import seed_accounts

        with Session(engine) as db:
            credentials = seed_accounts(db)
        for email, password in credentials:
            print(f"{email}: {password}")
        if not credentials:
            print("Existing local accounts preserved; passwords were not reset.")
        print("Start the backend with ENABLE_WORKER=false to keep the supplied data offline.")


if __name__ == "__main__":
    main()
