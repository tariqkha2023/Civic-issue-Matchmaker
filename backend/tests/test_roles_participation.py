from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_mvp import register, seed

from app.main import app
from app.migrations import migrate
from app.services import change_participation
from app.store import (
    AccountRole,
    ActiveClaim,
    AuditEntry,
    MaintainerAccess,
    MetadataCorrection,
    ParticipationEvent,
    Task,
    User,
    make_engine,
)


def grant(db_engine, uid, role, repo_id=None):
    with Session(db_engine) as db:
        db.add(AccountRole(user_id=uid, role=role))
        if repo_id:
            db.add(MaintainerAccess(user_id=uid, repository_id=repo_id))
        db.commit()


def test_public_signup_cannot_grant_privileges(client):
    result = client.post(
        "/api/accounts",
        json={
            "name": "Volunteer",
            "email": "public@example.com",
            "password": "correct horse battery",
            "roles": ["administrator"],
            "maintained_repositories": [1],
        },
    )
    assert result.status_code == 201
    assert result.json()["roles"] == ["volunteer"]
    for path in [
        "/api/admin/users",
        "/api/admin/repositories",
        "/api/admin/audit",
        "/api/maintainer/tasks",
    ]:
        assert client.get(path).status_code == 403
    assert (
        client.put(
            "/api/admin/users/1/roles", json={"roles": ["administrator"]}
        ).status_code
        == 403
    )
    assert (
        client.put("/api/admin/repositories/1", json={"enabled": False}).status_code
        == 403
    )


def test_maintainer_scope_correction_preserves_source_and_matching(client, db_engine):
    ids = seed(db_engine)
    user = register(client)
    with Session(db_engine) as db:
        repo_id = db.get(Task, ids[0]).repository_id
        original = dict(db.get(Task, ids[0]).metadata_fields)
    grant(db_engine, user["id"], "maintainer")
    body = {
        "skills": ["Gardening"],
        "topics": ["Environment"],
        "difficulty": "Beginner",
        "effort": 1,
    }
    assert client.get("/api/maintainer/tasks").json() == []
    assert (
        client.put(f"/api/maintainer/tasks/{ids[0]}/metadata", json=body).status_code
        == 403
    )
    with Session(db_engine) as db:
        db.add(MaintainerAccess(user_id=user["id"], repository_id=repo_id))
        db.commit()
    assert len(client.get("/api/maintainer/tasks").json()) == 4
    assert (
        client.put(f"/api/maintainer/tasks/{ids[0]}/metadata", json=body).status_code
        == 200
    )
    assert client.get("/api/recommendations?skill=gardening").json()["total"] == 1
    assert client.get(f"/api/tasks/{ids[0]}").json()["metadata"]["skills"] == [
        "gardening"
    ]
    assert client.get("/api/admin/users").status_code == 403
    with Session(db_engine) as db:
        assert db.get(Task, ids[0]).metadata_fields == original
        assert db.get(MetadataCorrection, ids[0]).fields["skills"] == ["gardening"]
        assert db.scalar(select(AuditEntry)).actor_id == user["id"]


def test_admin_assignments_source_controls_and_last_admin(client, db_engine):
    ids = seed(db_engine)
    admin = register(client, "admin@example.com")
    grant(db_engine, admin["id"], "administrator")
    with TestClient(app) as other:
        volunteer = register(other, "other@example.com")
        with Session(db_engine) as db:
            repo_id = db.get(Task, ids[0]).repository_id
        body = {"roles": ["maintainer"], "repository_ids": [repo_id]}
        assert (
            client.put(
                f"/api/admin/users/{volunteer['id']}/roles", json=body
            ).status_code
            == 200
        )
        assert "maintainer" in other.get("/api/me").json()["roles"]
        assert other.get("/api/maintainer/tasks").status_code == 200
        assert (
            client.put(
                f"/api/admin/users/{volunteer['id']}/roles",
                json={"roles": [], "repository_ids": [repo_id]},
            ).status_code
            == 422
        )
        assert (
            client.put(
                f"/api/admin/users/{volunteer['id']}/roles",
                json={"roles": ["maintainer"], "repository_ids": [999]},
            ).status_code
            == 422
        )
        assert (
            client.put(
                f"/api/admin/users/{admin['id']}/roles", json={"roles": []}
            ).status_code
            == 409
        )
        assert (
            client.put(
                f"/api/admin/repositories/{repo_id}", json={"enabled": False}
            ).status_code
            == 200
        )
        assert other.get("/api/recommendations").json()["total"] == 0
        assert (
            other.post(
                f"/api/tasks/{ids[0]}/participation", json={"action": "claimed"}
            ).status_code
            == 409
        )
        assert (
            client.put(
                f"/api/admin/repositories/{repo_id}", json={"enabled": True}
            ).status_code
            == 200
        )
        assert len(client.get("/api/admin/audit").json()) == 3
        assert (
            client.put(
                f"/api/admin/users/{volunteer['id']}/roles", json={"roles": []}
            ).status_code
            == 200
        )
        assert other.get("/api/maintainer/tasks").status_code == 403


def test_claims_release_completion_and_private_history(client, db_engine):
    ids = seed(db_engine)
    register(client)
    path = f"/api/tasks/{ids[0]}/participation"
    assert client.post(path, json={"action": "claimed"}).status_code == 200
    assert client.post(path, json={"action": "claimed"}).status_code == 200
    assert (
        client.get("/api/me/participation").json()["events"][0]["action"] == "claimed"
    )
    assert len(client.get("/api/me/participation").json()["events"]) == 1
    with TestClient(app) as other:
        register(other, "second@example.com")
        assert other.get("/api/me/participation").json() == {"active": [], "events": []}
        assert other.get(f"/api/tasks/{ids[0]}").json()["participation"]["claimed"]
        assert other.post(path, json={"action": "claimed"}).status_code == 409
        assert other.post(path, json={"action": "released"}).status_code == 409
        assert other.post(path, json={"action": "completed"}).status_code == 409
        assert client.post(path, json={"action": "released"}).status_code == 200
        assert other.post(path, json={"action": "claimed"}).status_code == 200
        assert other.post(path, json={"action": "completed"}).status_code == 200
        assert other.get("/api/me/participation").json()["active"] == []
        assert (
            other.get("/api/me/participation").json()["events"][0]["action"]
            == "completed"
        )
        assert other.post(path, json={"action": "claimed"}).status_code == 409
    assert (
        client.post(
            f"/api/tasks/{ids[2]}/participation", json={"action": "claimed"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/tasks/9999/participation", json={"action": "claimed"}
        ).status_code
        == 404
    )
    with Session(db_engine) as db:
        assert len(db.scalars(select(ParticipationEvent)).all()) == 4
        assert (
            db.get(Task, ids[0]).status == "open"
        )  # Completion does not rewrite the source.


def test_additive_migration_preserves_legacy_data(tmp_path):
    import sqlite3

    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(254), password_hash VARCHAR, profile JSON)"
        )
        connection.execute(
            "INSERT INTO users VALUES (1, 'old@example.com', 'existing-hash', '{\"name\": \"Original\"}')"
        )
    engine = make_engine("sqlite:///" + str(path))
    migrate(engine)
    migrate(engine)
    with Session(engine) as db:
        user = db.get(User, 1)
        assert user.profile["name"] == "Original"
        assert user.password_hash == "existing-hash"
        db.add_all(
            [ActiveClaim(task_id=1, user_id=1), ActiveClaim(task_id=1, user_id=2)]
        )
        with pytest.raises(IntegrityError):
            db.commit()
    engine.dispose()


def test_concurrent_claims_have_only_one_winner(tmp_path):
    engine = make_engine("sqlite:///" + str(tmp_path / "concurrent.db"))
    migrate(engine)
    ids = seed(engine)
    with Session(engine) as db:
        db.add_all(
            [
                User(email=f"{i}@example.com", password_hash="unused", profile={})
                for i in range(2)
            ]
        )
        db.commit()
        users = list(db.scalars(select(User.id)))

    def attempt(uid):
        with Session(engine) as db:
            try:
                change_participation(db, db.get(User, uid), ids[0], "claimed")
                return 200
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, users)) == [200, 409]
    with Session(engine) as db:
        assert len(db.scalars(select(ActiveClaim)).all()) == 1
        assert len(db.scalars(select(ParticipationEvent)).all()) == 1
    engine.dispose()
