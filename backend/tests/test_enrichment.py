"""Grounding, cache freshness, precedence and private-data boundaries."""

import json

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_mvp import register, seed

from app.enrichment import (
    MODEL,
    cached_fields,
    effective_metadata,
    fingerprint,
    interpret_requirements,
    run,
    validate_extraction,
)
from app.matching import score
from app.store import IssueEnrichment, Task


def raw(skill="python", quote="Improve Python"):
    return {
        "skills": [{"skill": skill, "evidence": quote}],
        "difficulty": None,
        "difficulty_evidence": None,
    }


def test_rejects_invented_quotes_and_unsupported_languages(db_engine):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[0])
        with pytest.raises(ValueError):
            validate_extraction(
                task, raw(quote="This nonexistent quotation mentions Python")
            )
        assert (
            validate_extraction(task, raw(quote="Improve public services"))["skills"]
            == []
        )
        assert validate_extraction(task, raw())["skills"] == ["python"]


def test_cache_invalidation_and_curator_precedence(db_engine):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[0])
        row = IssueEnrichment(
            task_id=task.id,
            content_hash=fingerprint(task),
            model=MODEL,
            fields=validate_extraction(task, raw()),
            updated_at=1,
        )
        assert effective_metadata(task, row)["ai_model"] == MODEL
        assert effective_metadata(task, row, {"skills": ["documentation"]})[
            "skills"
        ] == ["documentation"]
        task.description += " Updated source requirements."
        assert cached_fields(task, row) == {}
        assert "ai_model" not in effective_metadata(task, row)


def test_topic_and_repo_alone_never_produce_fit():
    meta = {
        "skills": [],
        "topics": ["civic participation"],
        "difficulty": None,
        "effort": None,
    }
    profile = {
        "skills": ["javascript"],
        "interests": ["civic participation"],
        "repositories": ["hackforla/website"],
    }
    assert score(profile, meta, "hackforla/website")[0] is None
    meta["skills"] = ["python"]
    value, explanation = score(profile, meta, "hackforla/website")
    assert value == 15
    assert any("python" in line for line in explanation)
    assert score({**profile, "repositories": []}, meta, "hackforla/website")[0] == value


def test_budgeted_extraction_sends_only_issue_text_and_reuses_cache(
    db_engine, monkeypatch
):
    ids = seed(db_engine)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert "test-secret" not in request.content.decode()
        assert "correct horse" not in request.content.decode()
        text = payload["messages"][-1]["content"]
        result = (
            {
                "skills": [
                    {
                        "skill": "python",
                        "basis": "explicit",
                        "rationale": "Python is named in the title",
                        "source_quote": "Improve Python",
                    }
                ],
                "difficulty": None,
                "difficulty_reason": None,
            }
            if "Improve Python" in text
            else {"skills": [], "difficulty": None, "difficulty_reason": None}
        )
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(result)}}],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "cost": 0.0001,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    assert run(10, 0.001, db_engine, transport)["enriched"] == 0
    result = run(10, 0.02, db_engine, transport)
    assert result["enriched"] == 3  # Open issues only; unknown results are cached too.
    assert len(requests) == 3
    assert run(10, 0.02, db_engine, transport)["enriched"] == 0
    assert len(requests) == 3
    with Session(db_engine) as db:
        row = db.get(IssueEnrichment, ids[0])
        assert row.fields["skills"] == ["python"]
        assert len(list(db.scalars(select(IssueEnrichment)))) == 3


def test_ai_metadata_used_by_discovery_and_invalidated_on_edit(client, db_engine):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[3])
        task.description = "Update the accessibility documentation"
        db.add(
            IssueEnrichment(
                task_id=task.id,
                model=MODEL,
                content_hash=fingerprint(task),
                fields=validate_extraction(task, raw("accessibility", "accessibility")),
                updated_at=1,
            )
        )
        db.commit()
    register(client)
    client.put(
        "/api/me/profile",
        json={"name": "Contributor", "skills": ["accessibility"], "hours": 5},
    )
    result = client.get("/api/recommendations?skill=accessibility").json()
    assert result["items"][0]["id"] == ids[3]
    assert result["items"][0]["score"] == 60
    assert "AI enriched" in result["items"][0]["metadata_origin"]
    assert client.get("/api/recommendations?q=accessibility").json()["total"] == 1
    with Session(db_engine) as db:
        db.get(Task, ids[3]).description = "Completely different issue"
        db.commit()
    assert client.get("/api/recommendations?skill=accessibility").json()["total"] == 0


def test_invalid_outputs_are_cached_without_skills_and_without_repeat_charges(
    db_engine, monkeypatch
):
    seed(db_engine)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(raw(quote="invented quotation"))
                        }
                    }
                ],
                "usage": {"cost": 0.0001},
            },
        )

    transport = httpx.MockTransport(handler)
    result = run(10, 0.02, db_engine, transport)
    assert result["rejected"] == 3
    with Session(db_engine) as db:
        rows = list(db.scalars(select(IssueEnrichment)))
        assert len(rows) == 3
        assert all(
            r.fields["status"] == "rejected" and not r.fields["skills"] for r in rows
        )
    assert run(10, 0.02, db_engine, transport)["enriched"] == 0
    assert len(calls) == 3


def test_provider_failure_stops_and_does_not_cache_fake_results(db_engine, monkeypatch):
    seed(db_engine)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")

    def handler(request):
        return httpx.Response(429, json={"error": "Do not expose upstream diagnostics"})

    result = run(10, 0.02, db_engine, httpx.MockTransport(handler), workers=1)
    assert result["rejected"] == 1
    with Session(db_engine) as db:
        assert list(db.scalars(select(IssueEnrichment))) == []


def test_feedback_orders_equal_fit_without_changing_percentages(client, db_engine):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        original = db.get(Task, ids[0])
        duplicate = Task(
            repository_id=original.repository_id,
            source_id="999",
            title="Another Python issue",
            description=original.description,
            url=original.url,
            status="open",
            labels=original.labels,
            metadata_fields=original.metadata_fields,
        )
        db.add(duplicate)
        db.commit()
        duplicate_id = duplicate.id
    register(client)
    client.put(
        "/api/me/profile",
        json={
            "name": "Contributor",
            "skills": ["python"],
            "interests": ["transportation"],
            "hours": 5,
        },
    )
    assert client.get("/api/recommendations").json()["items"][0]["id"] == ids[0]
    client.put(f"/api/tasks/{ids[0]}/feedback", json={"relevant": False})
    items = client.get("/api/recommendations").json()["items"]
    assert items[0]["id"] == duplicate_id
    assert items[0]["score"] == items[1]["score"] == 100


def test_comparison_can_disable_grounding_without_changing_production_default(
    db_engine,
):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[0])
        response = raw("react", "This quotation is not present in the issue")
        with pytest.raises(ValueError):
            validate_extraction(task, response)
        assert validate_extraction(task, response, check_evidence=False)["skills"] == [
            "react"
        ]
        # Basic output shape and difficulty enums remain required in both modes.
        with pytest.raises(ValueError):
            validate_extraction(
                task, {**response, "difficulty": "impossible"}, check_evidence=False
            )


def test_revised_prompt_keeps_inferred_skills_and_curator_overrides_them(db_engine):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[3])
        payload = {
            "skills": [
                {
                    "skill": "javascript",
                    "basis": "inferred",
                    "rationale": "Input normalization needs client-side logic.",
                    "source_quote": None,
                }
            ],
            "difficulty": None,
            "difficulty_reason": None,
        }
        fields = interpret_requirements(task, payload)
        assert fields["skills"] == ["javascript"]
        assert fields["evidence"][0]["basis"] == "inferred"
        row = IssueEnrichment(
            task_id=task.id,
            content_hash=fingerprint(task),
            model=MODEL,
            fields=fields,
            updated_at=1,
        )
        assert effective_metadata(task, row)["skill_weights"]["javascript"] == 0.5
        corrected = effective_metadata(task, row, {"skills": ["javascript"]})
        assert corrected["skill_weights"]["javascript"] == 1
        # Missing quotations affect provenance, not whether the skill survives.
        payload["skills"][0]["basis"] = "explicit"
        assert (
            interpret_requirements(task, payload)["evidence"][0]["basis"] == "inferred"
        )


def test_matching_inferred_skill_earns_half_the_points_of_a_stated_skill():
    profile = {"skills": ["python"]}
    meta = {
        "skills": ["python", "css"],
        "topics": [],
        "difficulty": None,
        "effort": None,
    }
    assert score(profile, meta, "civic/test")[0] == 30
    meta["skill_weights"] = {"python": 1, "css": 0.5}
    assert score(profile, meta, "civic/test")[0] == 30
    # Matching the inferred skill earns half the points of a stated skill.
    assert score({"skills": ["css"]}, meta, "civic/test")[0] == 15


def test_project_context_changes_invalidate_cached_interpretation(db_engine):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[0])
        project = {"languages": ["python"]}
        row = IssueEnrichment(
            task_id=task.id,
            content_hash=fingerprint(task, project),
            model=MODEL,
            fields={"skills": ["python"], "evidence": []},
            updated_at=1,
        )
        assert cached_fields(task, row, project)
        assert cached_fields(task, row, {"languages": ["perl"]}) == {}


def test_fixed_scale_prevents_sparse_matches_from_becoming_one_hundred_percent():
    profile = {
        "skills": ["javascript"],
        "interests": ["civic participation"],
        "level": "Beginner",
        "difficulty": "Beginner",
        "hours": 5,
    }
    meta = {
        "skills": ["javascript"],
        "topics": ["civic participation"],
        "difficulty": None,
        "effort": None,
    }
    assert score(profile, meta, "civic/project")[0] == 75
    meta["skill_weights"] = {"javascript": 0.5}
    assert score(profile, meta, "civic/project")[0] == 45
    meta.update(difficulty="Beginner", effort=5)
    assert score(profile, meta, "civic/project")[0] == 70
    meta["skill_weights"] = {"javascript": 1}
    assert score(profile, meta, "civic/project")[0] == 100
