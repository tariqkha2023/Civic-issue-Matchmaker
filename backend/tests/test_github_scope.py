import json
import time

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_mvp import register, seed

from app.github_sync import sync_source
from app.main import app
from app.migrations import migrate
from app.projects import configure_sources
from app.store import (
    AccountRole,
    ActiveClaim,
    Contribution,
    IssueInfo,
    LoginSession,
    MetadataCorrection,
    Repository,
    SourceSettings,
    Task,
    User,
)


def repo(db):
    row = Repository(
        source="github", path="civic/test", selection_labels=["ignore-this-whitelist"]
    )
    db.add(row)
    db.flush()
    db.add(SourceSettings(repository_id=row.id, fields={"topics": ["open mapping"]}))
    db.commit()
    return row


def issue(number=1, state="open"):
    return {
        "id": 100 + number,
        "number": number,
        "title": f"Issue {number}",
        "body": "Fix mapping UI",
        "html_url": f"https://github.com/civic/test/issues/{number}",
        "state": state,
        "labels": [{"name": "javascript"}],
        "assignees": [{"login": "upstream-person"}],
        "user": {"login": "reporter"},
        "updated_at": "2026-10-28T12:00:00Z",
    }


def transport(pages, calls=None, failure=None):
    def handler(request):
        if calls is not None:
            calls.append(str(request.url))
        if request.url.path == "/repos/civic/test":
            return httpx.Response(
                200,
                json={
                    "id": 42,
                    "full_name": "civic/test",
                    "html_url": "https://github.com/civic/test",
                },
            )
        page = int(request.url.params.get("page", "1"))
        if failure and page == failure:
            return httpx.Response(
                429,
                json={"message": "secret-token"},
                headers={"x-ratelimit-reset": str(int(time.time() + 3600))},
            )
        data = pages[page - 1]
        headers = (
            {
                "Link": f'<https://api.github.com/repos/civic/test/issues?state=all&page={page + 1}>; rel="next"'
            }
            if page < len(pages)
            else {}
        )
        return httpx.Response(200, json=data, headers=headers)

    return httpx.MockTransport(handler)


def test_tracker_stages_all_states_without_label_filters_and_resumes(db_engine):
    calls = []
    with Session(db_engine) as db:
        r = repo(db)
        pr = {**issue(3), "pull_request": {"url": "irrelevant"}}
        pages = [[issue(1), pr], [issue(2, "closed")]]
        assert (
            sync_source(db, r, max_pages=1, transport=transport(pages, calls))
            == "paused"
        )
        assert list(db.scalars(select(Task))) == []
        assert not db.get(SourceSettings, r.id).fields.get("complete")
        assert (
            sync_source(db, r, max_pages=1, transport=transport(pages, calls))
            == "completed"
        )
        tasks = list(db.scalars(select(Task)))
        assert len(tasks) == 2 and {t.status for t in tasks} == {"open", "closed"}
        assert db.get(IssueInfo, tasks[0].id).fields["assignees"] == ["upstream-person"]
        assert db.get(SourceSettings, r.id).fields["complete"]
        assert "state=all" in calls[1]
        assert all("labels=" not in u for u in calls)
        assert len([u for u in calls if u.endswith("/repos/civic/test")]) == 1


def test_failure_preserves_published_snapshot_and_progress_without_secret_leak(
    db_engine,
):
    with Session(db_engine) as db:
        r = repo(db)
        assert sync_source(db, r, transport=transport([[issue()]])) == "completed"
        task = db.scalar(select(Task))
        before = (task.title, r.last_success)
        settings = db.get(SourceSettings, r.id)
        settings.fields = {**settings.fields, "force_full": True}
        db.commit()
        changed = {**issue(), "title": "New unpublished title"}
        assert (
            sync_source(db, r, transport=transport([[changed], [issue(2)]], failure=2))
            == "failed"
        )
        db.refresh(task)
        db.refresh(r)
        assert (task.title, r.last_success) == before
        assert "secret-token" not in r.scan_error
        assert db.get(SourceSettings, r.id).fields["cursor"].endswith("page=2")
        assert (
            sync_source(db, r, transport=transport([[changed], [issue(2)]]))
            == "completed"
        )
        db.refresh(task)
        assert task.title == "New unpublished title"


def test_overlay_survives_source_refresh_and_marks_re_review(db_engine):
    with Session(db_engine) as db:
        r = repo(db)
        sync_source(db, r, transport=transport([[issue()]]))
        task = db.scalar(select(Task))
        db.add(
            MetadataCorrection(
                task_id=task.id,
                fields={"skills": ["documentation"], "rationale": "Review"},
            )
        )
        db.commit()
        sync_source(
            db, r, transport=transport([[{**issue(), "body": "Changed source text"}]])
        )
        assert db.get(MetadataCorrection, task.id).fields["skills"] == ["documentation"]
        assert db.get(MetadataCorrection, task.id).fields["needs_review"]
        assert task.metadata_fields["skills"] == ["javascript"]


def test_nonexclusive_tracking_submission_validation_privacy_and_source_authority(
    client, db_engine
):
    ids = seed(db_engine)
    register(client)
    assert (
        client.post(
            f"/api/tasks/{ids[0]}/participation", json={"action": "claimed"}
        ).status_code
        == 409
    )
    activity = client.post(f"/api/tasks/{ids[0]}/contributions").json()
    with TestClient(app) as other:
        register(other, "second@example.com")
        assert other.post(f"/api/tasks/{ids[0]}/contributions").status_code == 201
        assert (
            other.put(
                f"/api/me/contributions/{activity['id']}", json={"state": "in_progress"}
            ).status_code
            == 404
        )
    url = f"/api/me/contributions/{activity['id']}"
    assert (
        client.put(url, json={"state": "completed", "note": "Done"}).status_code == 409
    )
    assert client.put(url, json={"state": "in_progress"}).status_code == 200
    assert client.put(url, json={"state": "submitted"}).status_code == 422
    assert (
        client.put(
            url, json={"state": "submitted", "evidence": "https://evil.example/pull/1"}
        ).status_code
        == 422
    )
    assert (
        client.put(
            url,
            json={
                "state": "submitted",
                "evidence": "https://github.com/civic/transit/pull/1",
            },
        ).status_code
        == 200
    )
    assert (
        client.put(
            url,
            json={
                "state": "completed",
                "note": "Implemented and submitted; self-reported.",
            },
        ).status_code
        == 200
    )
    assert client.get("/api/me/contributions").json()[0]["state"] == "completed"
    with Session(db_engine) as db:
        assert db.get(Task, ids[0]).status == "open"
        assert list(db.scalars(select(ActiveClaim))) == []


def test_feedback_is_private_without_changing_skill_fit_and_export_omits_secrets(client, db_engine):
    ids = seed(db_engine)
    register(client)
    client.put(
        "/api/me/profile",
        json={
            "name": "Contributor",
            "skills": ["python"],
            "interests": ["transportation"],
            "hours": 3,
        },
    )
    before = client.get(f"/api/tasks/{ids[0]}").json()["score"]
    assert (
        client.put(
            f"/api/tasks/{ids[0]}/feedback",
            json={"relevant": False, "explanation": "Not suitable"},
        ).status_code
        == 200
    )
    assert client.get(f"/api/tasks/{ids[0]}").json()["score"] == before
    with TestClient(app) as other:
        register(other, "feedback-other@example.com")
        assert other.get("/api/me/feedback").json() == []
    data = client.get("/api/me/export").json()
    assert data["feedback"][0]["explanation"] == "Not suitable"
    assert "password_hash" not in json.dumps(data) and "token_hash" not in json.dumps(
        data
    )


def test_reauthenticated_deletion_anonymizes_invalidates_and_retains_source(
    client, db_engine
):
    ids = seed(db_engine)
    user = register(client)
    client.post(f"/api/tasks/{ids[0]}/contributions")
    assert (
        client.request("DELETE", "/api/me", json={"password": "wrong"}).status_code
        == 403
    )
    assert (
        client.request(
            "DELETE", "/api/me", json={"password": "correct horse battery"}
        ).status_code
        == 204
    )
    assert client.get("/api/me").status_code == 401
    with Session(db_engine) as db:
        assert db.get(User, user["id"]).profile["deleted"]
        assert "volunteer@example.com" != db.get(User, user["id"]).email
        assert list(db.scalars(select(Contribution))) == []
        assert db.get(Task, ids[0])
        assert list(db.scalars(select(LoginSession))) == []


def test_admin_sources_and_curator_scope(client, db_engine):
    user = register(client)
    assert (
        client.post("/api/admin/sources", json={"path": "org/repo"}).status_code == 403
    )
    with Session(db_engine) as db:
        db.add(AccountRole(user_id=user["id"], role="administrator"))
        db.commit()
    assert (
        client.post(
            "/api/admin/sources", json={"path": "https://evil.example"}
        ).status_code
        == 422
    )
    r = client.post("/api/admin/sources", json={"path": "org/repo"})
    assert r.status_code == 201
    assert (
        client.post("/api/admin/sources", json={"path": "ORG/REPO"}).status_code == 409
    )
    assert client.post(f"/api/admin/sources/{r.json()['id']}/scan").status_code == 202
    assert client.get("/api/admin/scans").status_code == 200


def test_daily_backup_restore(tmp_path):
    import sqlite3

    from app.store import make_engine
    from app.worker import backup_sqlite

    db_engine = make_engine("sqlite:///" + str(tmp_path / "original.db"))
    migrate(db_engine)
    with Session(db_engine) as db:
        db.add(User(email="backup@example.com", password_hash="unused", profile={}))
        db.commit()
    backup = backup_sqlite(db_engine, tmp_path / "backups")
    with sqlite3.connect(backup) as db:
        assert (
            db.execute("SELECT email FROM users").fetchone()[0] == "backup@example.com"
        )
    db_engine.dispose()


def test_legacy_activity_migration_retains_old_events(tmp_path):
    from app.store import Base, ParticipationEvent, make_engine

    db_engine = make_engine("sqlite:///" + str(tmp_path / "migration.db"))
    Base.metadata.create_all(db_engine)
    ids = seed(db_engine)
    with Session(db_engine) as db:
        u = User(email="old@example.com", password_hash="unused", profile={})
        db.add(u)
        db.flush()
        db.add(ParticipationEvent(user_id=u.id, task_id=ids[0], action="completed"))
        db.commit()
    migrate(db_engine)
    migrate(db_engine)
    with Session(db_engine) as db:
        rows = list(db.scalars(select(Contribution)))
        assert len(rows) == 1 and rows[0].state == "completed"
        assert len(db.scalars(select(ParticipationEvent)).all()) == 1
    db_engine.dispose()


def test_delivery_dedup_preferences_and_private_bookmark_history(client, db_engine):
    from app.events import deliver
    from app.store import EventDelivery, Notification

    user = register(client)
    ids = seed(db_engine)
    with Session(db_engine) as db:
        deliver(db, user["id"], "same-event", "One event")
        deliver(db, user["id"], "same-event", "One event")
        db.commit()
        assert (
            len(
                db.scalars(
                    select(EventDelivery).where(
                        EventDelivery.key == f"{user['id']}:same-event"
                    )
                ).all()
            )
            == 1
        )
        assert (
            len(
                db.scalars(
                    select(Notification).where(Notification.title == "One event")
                ).all()
            )
            == 1
        )
    client.put(
        "/api/me/preferences",
        json={"new_matches": False, "activity": False, "minimum_score": 80},
    )
    assert client.put(f"/api/me/saved/{ids[0]}").status_code == 204
    assert client.delete(f"/api/me/saved/{ids[0]}").status_code == 204
    assert [
        e["action"] for e in client.get("/api/me/participation").json()["events"]
    ] == ["unsaved", "saved"]
    with Session(db_engine) as db:
        assert db.scalar(
            select(EventDelivery).where(EventDelivery.status == "suppressed")
        )


def test_last_admin_deletion_denied_and_other_messages_private(client, db_engine):
    user = register(client)
    with Session(db_engine) as db:
        db.add(AccountRole(user_id=user["id"], role="administrator"))
        db.commit()
    assert (
        client.request(
            "DELETE", "/api/me", json={"password": "correct horse battery"}
        ).status_code
        == 409
    )
    assert client.get("/api/me").status_code == 200
    with TestClient(app) as a, TestClient(app) as b:
        ua = register(a, "private-a@example.com")
        ub = register(b, "private-b@example.com")
        assert a.get(f"/api/messages/{ub['id']}").status_code == 403
        assert b.get(f"/api/messages/{ua['id']}").status_code == 403


def test_source_disablement_and_unavailable_records_reject_new_tracking(
    client, db_engine
):
    ids = seed(db_engine)
    register(client)
    with Session(db_engine) as db:
        db.add(IssueInfo(task_id=ids[0], fields={"available": False}))
        db.commit()
    assert client.post(f"/api/tasks/{ids[0]}/contributions").status_code == 409
    with Session(db_engine) as db:
        db.get(Repository, db.get(Task, ids[1]).repository_id).enabled = False
        db.commit()
    assert client.post(f"/api/tasks/{ids[1]}/contributions").status_code == 409


def test_source_configuration_is_idempotent(db_engine):
    with Session(db_engine) as db:
        configure_sources(db)
        configure_sources(db)
        assert len(db.scalars(select(Repository)).all()) == 5
        assert len(db.scalars(select(SourceSettings)).all()) == 5


def test_github_repository_id_pagination_is_allowed_only_for_configured_id(db_engine):
    def handler(request):
        if request.url.path == "/repos/civic/test":
            return httpx.Response(
                200,
                json={
                    "id": 42,
                    "full_name": "civic/test",
                    "html_url": "https://github.com/civic/test",
                },
            )
        if request.url.path == "/repos/civic/test/issues":
            return httpx.Response(
                200,
                json=[issue(1)],
                headers={
                    "Link": '<https://api.github.com/repositories/42/issues?state=all&page=2>; rel="next"'
                },
            )
        assert request.url.path == "/repositories/42/issues"
        return httpx.Response(200, json=[issue(2, "closed")])

    with Session(db_engine) as db:
        r = repo(db)
        assert sync_source(db, r, transport=httpx.MockTransport(handler)) == "completed"
        assert len(db.scalars(select(Task)).all()) == 2
        row = db.get(SourceSettings, r.id)
        row.fields = {
            **row.fields,
            "cursor": "https://api.github.com/repositories/999/issues?page=3",
        }
        db.commit()
        assert sync_source(db, r, transport=httpx.MockTransport(handler)) == "failed"
        assert "Unsafe pagination" in r.scan_error
        assert len(db.scalars(select(Task)).all()) == 2


def test_scan_checkpoint_preserves_admin_owned_settings(db_engine):
    from app.github_sync import save_checkpoint

    with Session(db_engine) as db:
        r = repo(db)
        row = db.get(SourceSettings, r.id)
        old = dict(row.fields)
        row.fields = {**row.fields, "name": "Updated project", "interval_minutes": 120}
        db.commit()
        config = {**old, "pages": 3, "cursor": "next-page"}
        save_checkpoint(db, row, config)
        db.commit()
        assert row.fields["name"] == "Updated project"
        assert row.fields["interval_minutes"] == 120
        assert row.fields["pages"] == 3


def test_repository_rename_redirect_retains_issue_identity(db_engine):
    def moved(request):
        if request.url.path == "/repos/civic/test":
            return httpx.Response(
                301, headers={"Location": "https://api.github.com/repositories/42"}
            )
        if request.url.path == "/repositories/42":
            return httpx.Response(
                200,
                json={
                    "id": 42,
                    "full_name": "civic/renamed",
                    "html_url": "https://github.com/civic/renamed",
                },
            )
        assert request.url.path == "/repos/civic/renamed/issues"
        return httpx.Response(
            200,
            json=[{**issue(), "html_url": "https://github.com/civic/renamed/issues/1"}],
        )

    with Session(db_engine) as db:
        r = repo(db)
        sync_source(db, r, transport=transport([[issue()]]))
        original_id = db.scalar(select(Task.id))
        assert sync_source(db, r, transport=httpx.MockTransport(moved)) == "completed"
        assert r.path == "civic/renamed"
        assert db.scalar(select(Task.id)) == original_id
        assert len(db.scalars(select(Task)).all()) == 1


def test_private_source_is_never_published(db_engine):
    def private(request):
        return httpx.Response(
            200,
            json={
                "id": 42,
                "full_name": "civic/test",
                "html_url": "https://github.com/civic/test",
                "private": True,
            },
        )

    with Session(db_engine) as db:
        r = repo(db)
        assert sync_source(db, r, transport=httpx.MockTransport(private)) == "failed"
        assert "Only public" in r.scan_error
        assert list(db.scalars(select(Task))) == []


def test_deleted_accounts_cannot_receive_privileged_roles(client, db_engine):
    admin = register(client, "active-admin@example.com")
    with Session(db_engine) as db:
        db.add(AccountRole(user_id=admin["id"], role="administrator"))
        deleted = User(
            email="deleted@example.com",
            password_hash="unused",
            profile={"deleted": True},
        )
        db.add(deleted)
        db.commit()
        target = deleted.id
    assert (
        client.put(
            f"/api/admin/users/{target}/roles", json={"roles": ["administrator"]}
        ).status_code
        == 410
    )
