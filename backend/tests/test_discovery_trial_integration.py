import json
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.orm import Session
from test_mvp import register

from app.discovery_context import reviewed_context
from app.enrichment import effective_metadata
from app.matching import derive_metadata
from app.store import Repository, Task


def test_saved_research_search_scoring_and_curator_precedence(client, db_engine):
    samples = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs/interpretation-trial/context-review.json"
        ).read_text()
    )["issues"]
    sample = next(x for x in samples if x["id"] == 21550)
    register(client)
    profile = client.get("/api/me").json()["profile"]
    profile["skills"] = ["frontend development"]
    assert client.put("/api/me/profile", json=profile).status_code == 200
    with Session(db_engine) as db:
        repo = Repository(source="github", path="openstreetmap/iD")
        db.add(repo)
        db.flush()
        task = Task(
            repository_id=repo.id,
            source_id="8695",
            title=sample["title"],
            description=sample["description"],
            url=sample["url"],
            status="open",
            labels=[],
            metadata_fields=derive_metadata([]),
        )
        db.add(task)
        db.commit()
        task_id = task.id
    result = client.get(
        "/api/recommendations", params={"q": "frontend", "sort": "relevance"}
    ).json()
    assert result["total"] == 1
    assert client.get("/api/recommendations", params={"researched_only": True}).json()["total"] == 1
    item = result["items"][0]
    assert item["reviewed_context"]["background"] == sample["background"]
    assert item["metadata"]["skill_weights"]["frontend development"] == 0.5
    assert item["score"] == 50
    without_suggestions = client.get(
        "/api/recommendations", params={"include_suggested": False}
    ).json()["items"][0]
    assert without_suggestions["score"] == item["score"]
    assert item["search_match"] == "suggested_skill"
    assert (
        client.get(
            "/api/recommendations", params={"q": "frontend", "include_suggested": False}
        ).json()["total"]
        == 0
    )
    assert (
        client.get(
            "/api/recommendations",
            params={"skill": "front-end", "include_suggested": True},
        ).json()["total"]
        == 1
    )
    assert (
        client.get(
            "/api/recommendations",
            params={"skill": "frontend", "include_suggested": False},
        ).json()["total"]
        == 0
    )
    # Project explanations are searchable, while uncertainty and citations are not.
    assert (
        client.get("/api/recommendations", params={"q": "bench"}).json()["items"][0][
            "search_match"
        ]
        == "background"
    )
    assert (
        client.get("/api/recommendations", params={"q": "treatment"}).json()["total"]
        == 0
    )
    assert client.get(f"/api/tasks/{task_id}").json()["metadata"] == item["metadata"]
    with Session(db_engine) as db:
        task = db.get(Task, task_id)
        corrected = effective_metadata(task, correction={"skills": ["python"]})
        assert corrected["skills"] == ["python"]
        task.description += " Updated requirement."
        db.commit()
    changed = client.get(f"/api/tasks/{task_id}").json()
    assert changed["reviewed_context"] is None
    assert client.get("/api/recommendations", params={"researched_only": True}).json()["total"] == 0
    assert changed["metadata"]["skills"] == []


def test_review_identity_does_not_depend_on_local_database_id():
    samples = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs/interpretation-trial/context-review.json"
        ).read_text()
    )["issues"]
    sample = samples[0]
    task = SimpleNamespace(
        id=999999, **{k: sample[k] for k in ["title", "description", "url"]}
    )
    assert reviewed_context(task)["summary"] == sample["summary"]
    task.url += "0"
    assert reviewed_context(task) is None
