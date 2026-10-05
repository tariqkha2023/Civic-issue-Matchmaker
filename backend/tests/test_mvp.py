import time

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.models import RepositoryTask
from app.ingestion import scan_repository
from app.main import app
from app.matching import derive_metadata, score
from app.security import token_hash
from app.store import LoginSession, Repository, Task, User


def register(client, email="volunteer@example.com"):
    response = client.post(
        "/api/accounts",
        json={"name": "Volunteer", "email": email, "password": "correct horse battery"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def seed(db_engine):
    with Session(db_engine) as db:
        repo = Repository(
            source="github", path="civic/transit", last_success=time.time()
        )
        db.add(repo)
        db.flush()
        tasks = [
            Task(
                repository_id=repo.id,
                source_id=str(i),
                title=title,
                description="Improve public services",
                url=f"https://github.com/civic/transit/issues/{i}",
                status=status,
                labels=labels,
                metadata_fields=derive_metadata(labels),
            )
            for i, title, status, labels in [
                (
                    1,
                    "Improve Python transit API",
                    "open",
                    ["python", "topic:Transportation", "beginner", "effort:2h"],
                ),
                (
                    2,
                    "Build React dashboard",
                    "open",
                    ["react", "advanced", "effort:30h"],
                ),
                (3, "Closed issue", "closed", ["python"]),
                (4, "Unknown metadata", "open", []),
            ]
        ]
        db.add_all(tasks)
        db.commit()
        return [t.id for t in tasks]


def test_account_session_and_validation(client, db_engine):
    assert client.get("/api/me").status_code == 401
    created = register(client, "Volunteer@Example.com")
    assert created["email"] == "volunteer@example.com"
    cookie = client.cookies.get("civic_session")
    assert (
        "HttpOnly"
        in client.post(
            "/api/sessions",
            json={"email": created["email"], "password": "correct horse battery"},
        ).headers["set-cookie"]
    )
    assert (
        client.post(
            "/api/accounts",
            json={
                "name": "Other",
                "email": created["email"],
                "password": "another strong password",
            },
        ).status_code
        == 409
    )
    assert (
        client.put(
            "/api/me/profile", json={"name": "Volunteer", "hours": -1}
        ).status_code
        == 422
    )
    with Session(db_engine) as db:
        user = db.get(User, created["id"])
        assert "correct horse battery" not in user.password_hash
        assert cookie != db.get(LoginSession, token_hash(cookie)).token_hash
    assert client.delete("/api/sessions").status_code == 204
    assert client.get("/api/me").status_code == 401
    assert (
        client.post(
            "/api/sessions",
            json={"email": created["email"], "password": "wrong password!"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/sessions",
            json={"email": created["email"], "password": "correct horse battery"},
        ).status_code
        == 200
    )


def test_expiry_and_cross_site_protection(client, db_engine):
    register(client)
    token = client.cookies.get("civic_session")
    with Session(db_engine) as db:
        db.get(LoginSession, token_hash(token)).last_activity = time.time() - 1801
        db.commit()
    assert client.get("/api/me").status_code == 401
    assert (
        client.post(
            "/api/accounts", json={}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/accounts", json={}, headers={"Sec-Fetch-Site": "cross-site"}
        ).status_code
        == 403
    )


def test_recommendations_filters_detail_and_private_saves(client, db_engine):
    ids = seed(db_engine)
    register(client)
    profile = {
        "name": "Volunteer",
        "skills": ["Python"],
        "interests": ["Transportation"],
        "level": "Beginner",
        "difficulty": "Beginner",
        "hours": 3,
    }
    assert client.put("/api/me/profile", json=profile).status_code == 200
    result = client.get("/api/recommendations").json()
    assert result["total"] == 3
    assert result["items"][0]["id"] == ids[0]
    assert result["items"][0]["score"] == 100
    assert len(result["items"][0]["explanations"]) >= 2
    assert result["items"][-1]["score"] is None
    for params in [
        "skill=python",
        "topic=Transportation",
        "difficulty=Beginner",
        "max_effort=3",
        "q=Python",
    ]:
        assert client.get("/api/recommendations?" + params).json()["total"] == 1
    assert (
        client.get("/api/recommendations?status=closed").json()["items"][0]["id"]
        == ids[2]
    )
    assert (
        client.get("/api/recommendations?page_size=1&page=2").json()["items"][0]["id"]
        == ids[1]
    )
    assert client.get("/api/tasks/9999").status_code == 404
    assert client.put(f"/api/me/saved/{ids[0]}").status_code == 204
    assert client.put(f"/api/me/saved/{ids[0]}").status_code == 204
    assert client.put(f"/api/me/saved/{ids[2]}").status_code == 409
    assert client.get("/api/me/saved").json()[0]["id"] == ids[0]
    assert client.get(f"/api/tasks/{ids[0]}").json()["saved"]
    # Independent browser sessions must not share profile or saved records.
    with TestClient(app) as other:
        register(other, "other@example.com")
        assert other.get("/api/me/saved").json() == []
        assert other.get("/api/me").json()["profile"]["skills"] == []
        assert other.delete(f"/api/me/saved/{ids[0]}").status_code == 204
    assert len(client.get("/api/me/saved").json()) == 1
    client.delete("/api/sessions")
    client.post(
        "/api/sessions",
        json={"email": "volunteer@example.com", "password": "correct horse battery"},
    )
    assert client.get("/api/me").json()["profile"]["skills"] == ["python"]
    assert len(client.get("/api/me/saved").json()) == 1
    assert client.delete(f"/api/me/saved/{ids[0]}").status_code == 204
    assert client.get("/api/me/saved").json() == []


def test_scoring_unknown_and_preference():
    meta = derive_metadata(
        ["good first issue", "skill:python", "topic:Transportation", "effort:4h"]
    )
    strong = {
        "skills": ["python"],
        "interests": ["transportation"],
        "level": "Beginner",
        "difficulty": "Beginner",
        "hours": 4,
    }
    weak = {**strong, "skills": ["react"], "interests": ["health"], "hours": 1}
    assert (
        score(strong, meta, "civic/transit")[0] > score(weak, meta, "civic/transit")[0]
    )
    assert score(strong, derive_metadata([]), "civic/transit")[0] is None
    assert derive_metadata(["bug"])["effort"] is None
    assert (
        score({**strong, "difficulty": "Advanced"}, meta, "civic/transit")[0]
        < score(strong, meta, "civic/transit")[0]
    )


def test_scan_idempotency_closure_and_failure_preserves_cache(db_engine, monkeypatch):
    with Session(db_engine) as db:
        repo = Repository(source="github", path="civic/transit")
        db.add(repo)
        db.commit()
        imported = RepositoryTask(
            "github",
            "123",
            "Original",
            "Description",
            "https://github.com/civic/transit/issues/1",
            "open",
            ["python"],
        )
        monkeypatch.setattr(
            "app.ingestion.GitHubConnector.fetch_tasks", lambda self: [imported]
        )
        assert scan_repository(db, repo) == 1
        assert scan_repository(db, repo) == 1
        assert len(db.scalars(select(Task)).all()) == 1
        stamp = repo.last_success

        def failure(self):
            raise httpx.ConnectError("secret-token-must-not-leak")

        monkeypatch.setattr("app.ingestion.GitHubConnector.fetch_tasks", failure)
        try:
            scan_repository(db, repo)
            assert False, "Expected failed scan"
        except RuntimeError as exc:
            assert "secret-token" not in str(exc)
        assert db.scalar(select(Task)).title == "Original"
        assert repo.last_success == stamp
        assert repo.scan_error
        # A partially parsed scan must roll back earlier inserts/updates too.
        bad = RepositoryTask(
            "github", "456", "Bad URL", "", "http://evil.example", "open", []
        )
        imported.title = "Changed"
        monkeypatch.setattr(
            "app.ingestion.GitHubConnector.fetch_tasks", lambda self: [imported, bad]
        )
        try:
            scan_repository(db, repo)
        except RuntimeError:
            pass
        assert db.scalar(select(Task)).title == "Original"
        assert len(db.scalars(select(Task)).all()) == 1
        monkeypatch.setattr(
            "app.ingestion.GitHubConnector.fetch_tasks", lambda self: []
        )
        scan_repository(db, repo)
        assert db.scalar(select(Task)).status == "closed"
        assert repo.scan_error is None


def test_login_rate_limit_and_audit(client, db_engine):
    from app.store import AuthEvent

    register(client)
    for _ in range(10):
        assert (
            client.post(
                "/api/sessions",
                json={
                    "email": "volunteer@example.com",
                    "password": "incorrect password",
                },
            ).status_code
            == 401
        )
    response = client.post(
        "/api/sessions",
        json={"email": "volunteer@example.com", "password": "correct horse battery"},
    )
    assert response.status_code == 429
    assert response.headers["retry-after"] == "900"
    with Session(db_engine) as db:
        events = db.scalars(select(AuthEvent)).all()
        assert len(events) == 11
        assert events[0].actor_id is not None
        assert all("password" not in str(event.subject_hash) for event in events)


def test_disk_persistence_across_engines(tmp_path):
    from app.store import Base, SavedTask, make_engine

    url = "sqlite:///" + str(tmp_path / "restart.db")
    first = make_engine(url)
    Base.metadata.create_all(first)
    with Session(first) as db:
        user = User(
            email="persist@example.com",
            password_hash="unused",
            profile={"name": "Persisted"},
        )
        repo = Repository(source="github", path="civic/test")
        db.add_all([user, repo])
        db.flush()
        task = Task(
            repository_id=repo.id,
            source_id="1",
            title="Persisted issue",
            description="",
            url="https://github.com/civic/test/issues/1",
            status="open",
            labels=[],
            metadata_fields=derive_metadata([]),
        )
        db.add(task)
        db.flush()
        db.add(SavedTask(user_id=user.id, task_id=task.id))
        db.commit()
    first.dispose()
    second = make_engine(url)
    with Session(second) as db:
        assert db.scalar(select(User)).profile["name"] == "Persisted"
        assert db.scalar(select(Task)).title == "Persisted issue"
        assert db.scalar(select(SavedTask)) is not None
    second.dispose()


def test_source_selection_labels_and_reopening(db_engine, monkeypatch):
    with Session(db_engine) as db:
        repo = Repository(
            source="gitlab", path="civic/test", selection_labels=["good first issue"]
        )
        db.add(repo)
        db.commit()
        imported = RepositoryTask(
            "gitlab",
            "123",
            "Eligible",
            "",
            "https://gitlab.com/civic/test/-/issues/1",
            "opened",
            ["good first issue"],
        )
        other = RepositoryTask(
            "gitlab",
            "456",
            "Other",
            "",
            "https://gitlab.com/civic/test/-/issues/2",
            "opened",
            ["bug"],
        )
        monkeypatch.setattr(
            "app.ingestion.GitLabConnector.fetch_tasks", lambda self: [imported, other]
        )
        assert scan_repository(db, repo) == 1
        monkeypatch.setattr(
            "app.ingestion.GitLabConnector.fetch_tasks", lambda self: []
        )
        scan_repository(db, repo)
        assert db.scalar(select(Task)).status == "closed"
        monkeypatch.setattr(
            "app.ingestion.GitLabConnector.fetch_tasks", lambda self: [imported]
        )
        scan_repository(db, repo)
        assert db.scalar(select(Task)).status == "open"
        assert len(db.scalars(select(Task)).all()) == 1


def test_losing_eligibility_does_not_falsely_close_source_issue(
    client, db_engine, monkeypatch
):
    with Session(db_engine) as db:
        repo = Repository(
            source="github", path="civic/test", selection_labels=["good first issue"]
        )
        db.add(repo)
        db.commit()
        imported = RepositoryTask(
            "github",
            "1",
            "Still open",
            "",
            "https://github.com/civic/test/issues/1",
            "open",
            ["good first issue"],
        )
        monkeypatch.setattr(
            "app.ingestion.GitHubConnector.fetch_tasks", lambda self: [imported]
        )
        scan_repository(db, repo)
        imported.labels = ["bug"]
        assert scan_repository(db, repo) == 0
        assert db.scalar(select(Task)).status == "open"
    register(client)
    assert client.get("/api/recommendations").json()["total"] == 0


def test_operator_source_configuration(db_engine, monkeypatch):
    from app.manage import main

    monkeypatch.setattr("app.manage.engine", db_engine)

    def run(*args):
        monkeypatch.setattr("sys.argv", ["manage", *args])
        main()

    run("add-source", "github", "civic/test", "--label", "good first issue")
    run("add-source", "github", "civic/test", "--label", "documentation")
    with Session(db_engine) as db:
        repos = db.scalars(select(Repository)).all()
        assert len(repos) == 1
        assert repos[0].selection_labels == ["documentation"]
        repo_id = repos[0].id
    run("disable-source", str(repo_id))
    with Session(db_engine) as db:
        assert not db.get(Repository, repo_id).enabled
    run("add-source", "github", "civic/test")
    with Session(db_engine) as db:
        assert db.get(Repository, repo_id).enabled
        assert db.get(Repository, repo_id).selection_labels == []


def test_manual_tasks_are_shared_matched_and_saved(client, db_engine):
    body = {
        "title": "Improve community map",
        "project": "Community Mapping",
        "description": "Document routes",
        "skills": ["Kotlin", "Documentation"],
        "topic": "Transportation",
        "difficulty": "Beginner",
        "effort": 2,
    }
    assert client.post("/api/tasks/manual", json=body).status_code == 401
    register(client)
    response = client.post("/api/tasks/manual", json=body)
    assert response.status_code == 201, response.text
    task = response.json()
    assert task["source"] == "manual"
    assert task["url"] == ""
    assert task["metadata"]["skills"] == ["kotlin", "documentation"]
    assert task["metadata"]["effort"] == 2
    assert (
        client.post(
            "/api/tasks/manual", json={**body, "url": "javascript:alert(1)"}
        ).status_code
        == 422
    )
    assert (
        client.post("/api/tasks/manual", json={**body, "effort": -1}).status_code == 422
    )
    assert (
        client.post("/api/tasks/manual", json={**body, "title": "  "}).status_code
        == 422
    )
    # Project names reuse the same manual project without changing external sources.
    assert (
        client.post(
            "/api/tasks/manual",
            json={**body, "title": "Another task", "url": "https://example.com/issue"},
        ).status_code
        == 201
    )
    with Session(db_engine) as db:
        assert (
            len(
                db.scalars(
                    select(Repository).where(Repository.source == "manual")
                ).all()
            )
            == 1
        )
    client.delete("/api/sessions")
    register(client, "second@example.com")
    profile = {
        "name": "Second",
        "skills": ["Kotlin", "Documentation"],
        "interests": ["Transportation"],
        "hours": 3,
    }
    client.put("/api/me/profile", json=profile)
    result = client.get(
        "/api/recommendations?skill=kotlin&topic=Transportation&max_effort=3"
    ).json()
    assert result["total"] == 2
    assert result["items"][0]["score"] == 100
    assert client.get("/api/recommendations?q=kotlin").json()["total"] == 2
    assert client.put(f"/api/me/saved/{task['id']}").status_code == 204
    assert client.get("/api/me/saved").json()[0]["title"] == body["title"]


def test_demo_repository_seed_and_issue_creation(client, db_engine):
    from app.demo import DEMO_PATH, ISSUES, seed_demo

    with Session(db_engine) as db:
        assert seed_demo(db) == len(ISSUES)
        assert seed_demo(db) == 0
        assert len(db.scalars(select(Task)).all()) == len(ISSUES)
    body = {
        "title": "Serve meals at the community kitchen",
        "description": "Help serve dinner.",
        "skills": ["Food preparation", "Communication"],
        "topic": "Food security",
        "difficulty": "Beginner",
        "effort": 3,
        "location": "Community hall",
        "organizer": "Meals team",
    }
    assert client.post("/api/issues", json=body).status_code == 401
    register(client)
    client.put(
        "/api/me/profile",
        json={
            "name": "Volunteer",
            "skills": body["skills"],
            "interests": [body["topic"]],
            "hours": 3,
        },
    )
    response = client.post("/api/issues", json=body)
    assert response.status_code == 201, response.text
    issue = response.json()
    assert issue["repository"] == DEMO_PATH
    assert issue["source"] == "demo"
    assert issue["score"] == 100
    assert issue["metadata"]["location"] == "Community hall"
    assert not issue["metadata"]["demo_sample"]
    assert issue["url"] == ""
    with Session(db_engine) as db:
        assert seed_demo(db) == 0
        assert len(db.scalars(select(Task)).all()) == len(ISSUES) + 1
    listing = client.get(
        "/api/recommendations", params={"repository": DEMO_PATH, "q": body["title"]}
    ).json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == issue["id"]
    assert client.put(f"/api/me/saved/{issue['id']}").status_code == 204
    assert client.get("/api/me/saved").json()[0]["id"] == issue["id"]
