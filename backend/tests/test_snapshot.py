"""Public-only handoff, stable-ID restore, freshness and paid-cache reuse."""

import gzip
import hashlib
import json

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment import (
    MODEL,
    cached_fields,
    fingerprint,
    interpret_requirements,
    project_context,
    run,
)
from app.matching import derive_metadata
from app.snapshot import canonical, export_snapshot, import_snapshot, load_snapshot
from app.store import (
    AccountRole,
    AccountSettings,
    AuditEntry,
    Base,
    Contribution,
    IssueEnrichment,
    IssueInfo,
    LoginSession,
    MaintainerAccess,
    Message,
    MetadataCorrection,
    Notification,
    Repository,
    SavedTask,
    SourceSettings,
    Task,
    User,
    make_engine,
)

PRIVATE = "private-account-session-message-sentinel"
PROJECT = dict(name="Hack for LA", mission="Civic software", languages=["javascript"],
               topics=["civic participation"], github_id=234, github_url="https://github.com/hackforla/website",
               complete=True, interval_minutes=60, last_full=100)


def source_database(db_engine):
    with Session(db_engine) as db:
        repo = Repository(id=3, source="github", path="hackforla/website", last_success=100,
                          enabled=True, selection_labels=[])
        db.add(repo)
        db.flush()
        db.add(SourceSettings(repository_id=repo.id, fields={**PROJECT, "token": PRIVATE, "cursor": PRIVATE}))
        for tid, sid, number, status in [(5, "12345", 11, "open"), (6, "67890", 12, "closed")]:
            task = Task(id=tid, repository_id=repo.id, source_id=sid, title="Improve JavaScript navigation",
                        description="Improve civic participation software.", labels=["beginner"], status=status,
                        url=f"https://github.com/hackforla/website/issues/{number}", first_seen=50,
                        metadata_fields={**derive_metadata(["beginner"]), "topics": ["civic participation"], "user_id": PRIVATE})
            db.add(task)
            db.flush()
            db.add(IssueInfo(task_id=task.id, fields=dict(number=number, assignees=[], author="public-author",
                                                       updated_at="2026-10-28T00:00:00Z", available=True, email=PRIVATE)))
            if status == "open":
                fields = interpret_requirements(task, dict(skills=[dict(skill="javascript", basis="explicit",
                    rationale="JavaScript is named in the title.", source_quote="JavaScript")],
                    difficulty=None, difficulty_reason=None))
                fields["status"] = "accepted"
                fields["private_data"] = PRIVATE
                fields["evidence"][0]["user_id"] = PRIVATE
                db.add(IssueEnrichment(task_id=task.id, content_hash=fingerprint(task, project_context(PROJECT)),
                                       model=MODEL, fields=fields, cost=0.001, updated_at=90))
        db.add(User(email="private@example.com", password_hash=PRIVATE, profile={"secret": PRIVATE}))
        db.commit()


@pytest.fixture
def snapshot_file(db_engine, tmp_path):
    source_database(db_engine)
    path = tmp_path / "public.json.gz"
    export_snapshot(path, db_engine)
    return path


@pytest.fixture
def target(tmp_path):
    engine = make_engine("sqlite:///" + str(tmp_path / "target.db"))
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_export_allowlist_and_complete_public_sources_only(snapshot_file, db_engine):
    payload = gzip.decompress(snapshot_file.read_bytes())
    assert PRIVATE.encode() not in payload
    data = load_snapshot(snapshot_file)
    assert len(data.sources) == 1
    assert len(data.sources[0].issues) == 2
    assert data.sources[0].issues[0].enrichment.fields.evidence[0].quote == "JavaScript"
    assert "id" not in json.loads(payload)["data"]["sources"][0]
    manifest = json.loads(snapshot_file.with_name("public.manifest.json").read_text())
    assert manifest["gzip_sha256"] == hashlib.sha256(snapshot_file.read_bytes()).hexdigest()
    with Session(db_engine) as db:
        db.add(Repository(source="gitlab", path=PRIVATE, enabled=True))
        unfinished = Repository(source="github", path="example/unpublished", enabled=True)
        db.add(unfinished)
        db.flush()
        db.add(SourceSettings(repository_id=unfinished.id, fields={"complete": False, "token": PRIVATE}))
        db.commit()
    export_snapshot(snapshot_file, db_engine)
    assert len(load_snapshot(snapshot_file).sources) == 1


def test_clean_restore_is_repeatable_and_reuses_paid_cache_without_api_calls(snapshot_file, target, monkeypatch):
    result = import_snapshot(snapshot_file, target)
    assert result["created_issues"] == 2 and result["imported_caches"] == 1
    with Session(target) as db:
        ids = list(db.scalars(select(Task.id).order_by(Task.id)))
        assert list(db.scalars(select(User))) == []
        task = db.scalar(select(Task).where(Task.status == "open"))
        context = project_context(db.get(SourceSettings, task.repository_id).fields)
        assert cached_fields(task, db.get(IssueEnrichment, task.id), context)["skills"] == ["javascript"]
    repeated = import_snapshot(snapshot_file, target)
    assert repeated["created_issues"] == 0
    with Session(target) as db:
        assert list(db.scalars(select(Task.id).order_by(Task.id))) == ids
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only")

    def no_paid_requests(request):
        pytest.fail("A restored cache must not trigger a paid request")

    assert run(10, 0.02, target, httpx.MockTransport(no_paid_requests))["enriched"] == 0


def private_rows(db):
    return {model.__tablename__: [dict(row) for row in db.execute(select(model.__table__)).mappings()]
            for model in [User, LoginSession, AccountRole, AccountSettings, MaintainerAccess,
                          Message, Notification, AuditEntry, Contribution, SavedTask, MetadataCorrection]}


def test_existing_private_data_and_task_ids_survive_refresh_and_repeat_import(snapshot_file, target):
    with Session(target) as db:
        repo = Repository(id=91, source="github", path="hackforla/website", enabled=False, last_success=50,
                          selection_labels=["local setting"])
        db.add(repo)
        db.flush()
        db.add(SourceSettings(repository_id=repo.id, fields={**PROJECT, "interval_minutes": 180}))
        task = Task(id=301, repository_id=repo.id, source_id="12345", title="Older source text", description="",
                    url="https://github.com/hackforla/website/issues/11", status="open", labels=[], metadata_fields=derive_metadata([]))
        user = User(email="teammate@example.com", password_hash=PRIVATE, profile={"skills": ["javascript"]})
        db.add_all([task, user])
        db.flush()
        db.add_all([
            LoginSession(token_hash=PRIVATE, user_id=user.id), AccountRole(user_id=user.id, role="maintainer"),
            AccountSettings(user_id=user.id, preferences={"private": PRIVATE}),
            MaintainerAccess(user_id=user.id, repository_id=repo.id),
            Message(sender_id=user.id, recipient_id=user.id, body=PRIVATE), Notification(user_id=user.id, title=PRIVATE),
            AuditEntry(actor_id=user.id, action=PRIVATE, target=PRIVATE, details={}),
            Contribution(user_id=user.id, task_id=task.id, state="in_progress", note=PRIVATE, events=[{"note": PRIVATE}]),
            SavedTask(user_id=user.id, task_id=task.id), MetadataCorrection(task_id=task.id, fields={"rationale": PRIVATE}),
        ])
        db.commit()
        before = private_rows(db)
    for _ in range(2):
        import_snapshot(snapshot_file, target)
        with Session(target) as db:
            assert private_rows(db) == before
            task = db.scalar(select(Task).where(Task.source_id == "12345"))
            assert task.id == 301 and task.repository_id == 91
            assert task.title == "Improve JavaScript navigation"
            repo = db.get(Repository, 91)
            assert not repo.enabled and repo.selection_labels == ["local setting"]
            assert db.get(SourceSettings, 91).fields["interval_minutes"] == 180


def test_newer_issue_and_local_project_context_are_not_overwritten(snapshot_file, target):
    import_snapshot(snapshot_file, target)
    with Session(target) as db:
        task = db.scalar(select(Task).where(Task.status == "open"))
        task.title = "A newer upstream title"
        info = db.get(IssueInfo, task.id)
        info.fields = {**info.fields, "updated_at": "2026-10-29T00:00:00Z"}
        settings = db.get(SourceSettings, task.repository_id)
        settings.fields = {**settings.fields, "languages": ["typescript"]}
        db.commit()
    result = import_snapshot(snapshot_file, target)
    assert result["skipped_newer"] == 1 and result["skipped_caches"] == 1
    with Session(target) as db:
        task = db.scalar(select(Task).where(Task.status == "open"))
        assert task.title == "A newer upstream title"
        assert db.get(SourceSettings, task.repository_id).fields["languages"] == ["typescript"]


def test_corrupt_or_incompatible_snapshot_fails_before_writes(snapshot_file, target):
    original = json.loads(gzip.decompress(snapshot_file.read_bytes()))
    original["data"]["sources"][0]["issues"][0]["title"] = "Tampered"
    snapshot_file.write_bytes(gzip.compress(canonical(original)))
    with pytest.raises(ValueError, match="checksum"):
        import_snapshot(snapshot_file, target)
    original["sha256"] = hashlib.sha256(canonical(original["data"])).hexdigest()
    snapshot_file.write_bytes(gzip.compress(canonical(original)))
    with pytest.raises(ValueError, match="Cache does not match"):
        import_snapshot(snapshot_file, target)
    with Session(target) as db:
        assert list(db.scalars(select(Repository))) == []


def test_identity_conflict_rolls_back_existing_data(snapshot_file, target):
    envelope = json.loads(gzip.decompress(snapshot_file.read_bytes()))
    second = json.loads(json.dumps(envelope["data"]["sources"][0]))
    second["path"] = "example/website"
    second["project"]["github_id"] = 235
    second["project"]["github_url"] = "https://github.com/example/website"
    for issue in second["issues"]:
        issue["url"] = f"https://github.com/example/website/issues/{issue['upstream']['number']}"
    envelope["data"]["sources"].append(second)
    envelope["sha256"] = hashlib.sha256(canonical(envelope["data"])).hexdigest()
    snapshot_file.write_bytes(gzip.compress(canonical(envelope)))
    with Session(target) as db:
        repo = Repository(source="github", path="example/website", enabled=True)
        db.add(repo)
        db.flush()
        db.add(SourceSettings(repository_id=repo.id, fields={**PROJECT, "github_id": 999}))
        db.commit()
    with pytest.raises(ValueError, match="another upstream identity"):
        import_snapshot(snapshot_file, target)
    with Session(target) as db:
        assert list(db.scalars(select(Task))) == []
        assert [r.path for r in db.scalars(select(Repository))] == ["example/website"]
        assert db.scalar(select(SourceSettings)).fields["github_id"] == 999


def test_private_fields_in_import_are_rejected_even_with_valid_checksum(snapshot_file, target):
    envelope = json.loads(gzip.decompress(snapshot_file.read_bytes()))
    envelope["data"]["users"] = [{"email": PRIVATE}]
    envelope["sha256"] = hashlib.sha256(canonical(envelope["data"])).hexdigest()
    snapshot_file.write_bytes(gzip.compress(canonical(envelope)))
    with pytest.raises(ValueError):
        import_snapshot(snapshot_file, target)
    with Session(target) as db:
        assert list(db.scalars(select(Repository))) == []
        assert list(db.scalars(select(User))) == []
