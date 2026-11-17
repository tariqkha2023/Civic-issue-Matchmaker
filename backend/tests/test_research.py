"""Research collection, cost limits and real Discover integration, with no network."""

import base64
import copy
import json
import time

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_mvp import register, seed

from app.enrichment import MODEL, effective_metadata
from app.research import run
from app.research_collect import Collector
from app.research_schema import current_research, digest, validate_result
from app.store import IssueResearch, ResearchRun, Task


def github(request):
    path = request.url.path
    assert request.url.host == "api.github.com"
    assert "authorization" not in request.headers
    if path == "/repos/civic/transit":
        return httpx.Response(
            200, json={"private": False, "full_name": "civic/transit"}
        )
    if path.endswith("/readme"):
        return httpx.Response(
            200,
            json={
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(
                    b"This project helps residents find accessible bus journeys."
                ).decode(),
            },
        )
    if path.endswith("/comments"):
        return httpx.Response(
            200, json=[{"body": "The exact scope still needs discussion."}]
        )
    return httpx.Response(404)


def output(bundle):
    def claim(text, source):
        return {
            "text": text,
            "citations": [{"source": source["url"], "quote": source["text"]}],
        }

    return {
        "summary": claim("Improve the transit service.", bundle["sources"][0]),
        "background": claim(
            "Residents use this software to plan accessible bus journeys.",
            bundle["sources"][1],
        ),
        "motivation": None,
        "work": claim("Improve the transit API.", bundle["sources"][0]),
        "skills": [
            dict(
                claim(
                    "Python may help implement the requested API work.",
                    bundle["sources"][0],
                ),
                name="python",
            )
        ],
        "uncertainties": ["Uncertain deployment arrangements."],
    }


def collect(db_engine, ids, handler=github):
    return run(
        "collect",
        task_ids=ids,
        db_engine=db_engine,
        transport=httpx.MockTransport(handler),
    )


def save_result(db, task_id):
    row = db.get(IssueResearch, task_id)
    row.fields = {
        **row.fields,
        "result": output(row.fields["bundle"]),
        "result_hash": digest(row.fields["bundle"]),
        "model": MODEL,
        "generated_at": time.time(),
    }
    db.commit()
    return row


def test_collection_is_bounded_reuses_project_docs_and_has_no_ai(
    db_engine, monkeypatch
):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    ids = seed(db_engine)
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return github(request)

    assert collect(db_engine, ids[:2], handler)["collected"] == 2
    assert sum(url.endswith("/readme") for url in calls) == 1
    assert all(
        url.startswith("https://api.github.com/repos/civic/transit") for url in calls
    )
    with Session(db_engine) as db:
        row = db.get(IssueResearch, ids[0])
        assert len(row.fields["bundle"]["sources"]) == 3
        assert any(
            "Could not collect" in s for s in row.fields["bundle"]["limitations"]
        )
    calls.clear()
    assert collect(db_engine, ids[:2], handler)["skipped"] == 2
    assert calls == []


def test_rejects_private_repo_redirect_and_external_links(db_engine):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[0])
        task.description += " https://127.0.0.1/secret https://evil.test/docs https://github.com/other/private/blob/main/key"
        db.commit()
    assert collect(db_engine, ids[:1])["collected"] == 1
    for response in [
        httpx.Response(302, headers={"location": "http://127.0.0.1/"}),
        httpx.Response(200, json={"private": True, "full_name": "civic/transit"}),
    ]:
        result = run(
            "collect",
            task_ids=ids[:1],
            refresh=True,
            db_engine=db_engine,
            transport=httpx.MockTransport(lambda _: response),
        )
        assert result["rejected"] == 1


def test_grounding_unknowns_and_invented_skills(db_engine):
    ids = seed(db_engine)
    collect(db_engine, ids[:1])
    with Session(db_engine) as db:
        bundle = db.get(IssueResearch, ids[0]).fields["bundle"]
        result = output(bundle)
        result["skills"].append({**result["skills"][0], "name": "kubernetes"})
        validated = validate_result(result, bundle)
        assert [s["name"] for s in validated["skills"]] == ["python"]
        assert validated["motivation"] is None
        bad = copy.deepcopy(result)
        bad["background"]["citations"][0]["quote"] = (
            "A fabricated claim not present in any source."
        )
        with pytest.raises(ValueError):
            validate_result(bad, bundle)
        bad = copy.deepcopy(result)
        bad["work"]["citations"] = bad["background"]["citations"]
        with pytest.raises(ValueError):
            validate_result(bad, bundle)


def test_cache_invalidation_and_original_cache_compatibility(db_engine):
    ids = seed(db_engine)
    collect(db_engine, ids[:1])
    with Session(db_engine) as db:
        row = save_result(db, ids[0])
        task = db.get(Task, ids[0])
        assert current_research(task, row, {})
        assert current_research(task, row, {"mission": "changed"}) is None
        old = copy.deepcopy(row.fields)
        for field, value in [("version", "old"), ("expires_at", 0)]:
            data = copy.deepcopy(old)
            data["bundle"][field] = value
            row.fields = data
            assert current_research(task, row, {}) is None
        row.fields = old
        task.description += " source changed"
        assert current_research(task, row, {}) is None
        assert effective_metadata(task)["skills"] == ["python"]


def test_budget_key_requirement_provider_failure_and_resume(db_engine, monkeypatch):
    ids = seed(db_engine)
    collect(db_engine, ids[:2])
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError):
        run("interpret", budget=0.10, db_engine=db_engine)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    calls = []

    def provider(request):
        calls.append(request)
        assert request.url.host == "openrouter.ai"
        payload = json.loads(request.content)
        bundle = json.loads(payload["messages"][1]["content"])
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(output(bundle))}}],
                "usage": {},
            },
        )

    assert (
        run(
            "interpret",
            budget=0.001,
            db_engine=db_engine,
            transport=httpx.MockTransport(provider),
        )["attempted"]
        == 0
    )
    assert not calls
    result = run(
        "interpret",
        limit=1,
        budget=0.10,
        task_ids=ids[:1],
        db_engine=db_engine,
        transport=httpx.MockTransport(provider),
    )
    assert result["accepted"] == 1
    assert 0 < result["cost_upper_estimate"] <= 0.10
    assert (
        run(
            "interpret",
            budget=0.10,
            task_ids=ids[:1],
            db_engine=db_engine,
            transport=httpx.MockTransport(provider),
        )["attempted"]
        == 0
    )
    assert len(calls) == 1
    failed = run(
        "interpret",
        budget=0.10,
        task_ids=ids[1:2],
        db_engine=db_engine,
        transport=httpx.MockTransport(lambda _: httpx.Response(401)),
    )
    assert failed["status"] == "provider_error"
    assert failed["cost_upper_estimate"] > 0
    with Session(db_engine) as db:
        ledger = db.scalars(select(ResearchRun).order_by(ResearchRun.id.desc())).first()
        assert ledger.fields["status"] == "provider_error"


def test_real_api_search_projection_scoring_and_no_network(
    client, db_engine, monkeypatch
):
    ids = seed(db_engine)
    collect(db_engine, ids[:1])
    with Session(db_engine) as db:
        row = save_result(db, ids[0])
        task = db.get(Task, ids[0])
        # An inferred skill cannot override an explicit curator selection.
        assert effective_metadata(
            task, correction={"skills": ["documentation"]}, research=row
        )["skills"] == ["documentation"]
    register(client)
    profile = client.get("/api/me").json()["profile"]
    profile["skills"] = ["python"]
    client.put("/api/me/profile", json=profile)
    monkeypatch.setattr(
        httpx.HTTPTransport,
        "handle_request",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("Browsing must not fetch research")
        ),
    )
    response = client.get(
        "/api/recommendations", params={"q": "accessible bus journeys"}
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    item = response.json()["items"][0]
    assert item["reviewed_context"]["kind"] == "ai_research"
    assert item["reviewed_context"]["background"].startswith("Residents")
    assert item["score"] == 100
    assert (
        client.get(
            "/api/recommendations", params={"q": "deployment arrangements"}
        ).json()["total"]
        == 0
    )
    assert (
        client.get(f"/api/tasks/{ids[0]}").json()["reviewed_context"]
        == item["reviewed_context"]
    )
    with Session(db_engine) as db:
        task = db.get(Task, ids[0])
        task.description += " Updated."
        db.commit()
    assert (
        client.get(
            "/api/recommendations", params={"q": "accessible bus journeys"}
        ).json()["total"]
        == 0
    )


def test_inferred_skills_keep_half_weight_and_admin_audit(client, db_engine):
    from app.store import AccountRole

    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[3])
        task.description = "Fix keyboard navigation through the map controls."
        db.commit()
    collect(db_engine, ids[3:])
    with Session(db_engine) as db:
        row = db.get(IssueResearch, ids[3])
        result = output(row.fields["bundle"])
        result["skills"][0]["name"] = "accessibility"
        result["skills"][0]["text"] = (
            "Accessibility skills may help with keyboard navigation."
        )
        row.fields = {
            **row.fields,
            "result": result,
            "model": MODEL,
            "result_hash": digest(row.fields["bundle"]),
            "attempt_hash": digest(row.fields["bundle"]),
        }
        db.commit()
    register(client)
    me = client.get("/api/me").json()
    assert client.get("/api/admin/research").status_code == 403
    with Session(db_engine) as db:
        db.add(AccountRole(user_id=me["id"], role="administrator"))
        db.commit()
    counts = client.get("/api/admin/research").json()
    assert counts["with_background"] == counts["ai_backgrounds"] == 1
    assert counts["collected"] == 1
    assert counts["awaiting_interpretation"] == 0
    assert counts["latest_run"]["mode"] == "collect"
    item = client.get(f"/api/tasks/{ids[3]}").json()
    assert item["metadata"]["skill_weights"]["accessibility"] == 0.5
    assert (
        client.get("/api/recommendations", params={"skill": "accessibility"}).json()[
            "total"
        ]
        == 1
    )
    assert (
        client.get(
            "/api/recommendations",
            params={"skill": "accessibility", "include_suggested": False},
        ).json()["total"]
        == 0
    )


def test_collector_limits_binary_oversize_and_link_fetches(db_engine):
    ids = seed(db_engine)
    with Session(db_engine) as db:
        task = db.get(Task, ids[0])
        task.description += (
            "\nhttps://github.com/civic/transit/blob/main/docs/guide.md\n"
        )
        task.description += "\n".join(
            f"https://github.com/civic/transit/issues/{i}" for i in range(10, 30)
        )
        calls = []

        def handler(request):
            calls.append(request.url.path)
            if request.url.path.endswith("/readme"):
                return httpx.Response(200, content=b"x" * 128001)
            if request.url.path.endswith("/docs/guide.md"):
                return httpx.Response(
                    200,
                    json={
                        "type": "file",
                        "encoding": "base64",
                        "content": base64.b64encode(
                            b"Guide to transit routing for residents."
                        ).decode(),
                    },
                )
            return github(request)

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            bundle = Collector(db, client).collect(task, "civic/transit", {})
        assert (
            len(calls) <= 8
        )  # Public-repository verification plus seven source requests.
        assert any(s["url"].endswith("/docs/guide.md") for s in bundle["sources"])
        assert any("exceeded the collection limit" in s for s in bundle["limitations"])
        assert any("Could not collect" in s for s in bundle["limitations"])


def test_researched_filter_excludes_collection_only_missing_and_stale_backgrounds(client, db_engine):
    ids = seed(db_engine)
    collect(db_engine, ids[:2])
    register(client)
    assert client.get('/api/recommendations', params={'researched_only': True}).json()['total'] == 0
    with Session(db_engine) as db:
        save_result(db, ids[0])
    params = {'researched_only': True, 'page_size': 1}
    found = client.get('/api/recommendations', params=params).json()
    assert found['total'] == 1
    assert found['items'][0]['id'] == ids[0]
    assert found['items'][0]['source_skills'] == ['python']
    assert client.get('/api/recommendations', params={**params, 'page': 2}).json()['items'] == []
    assert client.get('/api/recommendations', params={**params, 'q': 'accessible bus journeys'}).json()['total'] == 1
    assert client.get('/api/recommendations', params={**params, 'skill': 'react'}).json()['total'] == 0
    with Session(db_engine) as db:
        row = db.get(IssueResearch, ids[0])
        data = copy.deepcopy(row.fields)
        data['result']['background'] = None
        row.fields = data
        db.commit()
    assert client.get('/api/recommendations', params=params).json()['total'] == 0
    with Session(db_engine) as db:
        save_result(db, ids[0])
        task = db.get(Task, ids[0])
        task.description += ' changed'
        db.commit()
    assert client.get('/api/recommendations', params=params).json()['total'] == 0
    assert client.get('/api/recommendations').json()['total'] == 3
