"""Offline interpretation, retrieval and compatibility contracts."""
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session
from test_mvp import register, seed
from test_snapshot import PROJECT, source_database
from test_snapshot import target as target

from app.enrichment import (
    LEGACY_VERSION,
    MODEL,
    cached_fields,
    effective_metadata,
    fingerprint,
    interpret_requirements,
    project_context,
)
from app.matching import derive_metadata, score
from app.snapshot import (
    DEFAULT_SNAPSHOT,
    export_snapshot,
    import_snapshot,
    load_snapshot,
)
from app.store import IssueEnrichment, Task

QUOTE = "The map cannot be used with a keyboard. Fix focus movement."


def interpretation():
    return {
        "summary": {"text": "Make the map usable without a mouse.", "source_quote": QUOTE},
        "objective": {"text": "Let people navigate the map using keys.", "source_quote": QUOTE},
        "activities": [{"text": "Repair focus movement.", "source_quote": "Fix focus movement."}],
        "concepts": [{"text": "accessible navigation", "basis": "inferred", "source_quote": QUOTE}],
        "uncertainties": ["The affected component and acceptance criteria are not specified."],
    }


def payload():
    return {"skills": [], "difficulty": None, "difficulty_reason": None,
            "interpretation": interpretation()}


def task():
    return SimpleNamespace(title="Map controls", description=QUOTE, labels=[],
                           project={}, metadata_fields=derive_metadata([]))


def test_interpretation_requires_real_quotes_and_bounded_fields():
    item = task()
    raw = payload()
    assert interpret_requirements(item, raw)["interpretation"] == interpretation()
    raw["interpretation"]["summary"]["source_quote"] = "Invented source text"
    with pytest.raises(ValueError):
        interpret_requirements(item, raw)
    raw = payload()
    raw["interpretation"]["activities"] *= 7
    with pytest.raises(ValueError):
        interpret_requirements(item, raw)
    raw = payload()
    raw["interpretation"]["concepts"][0]["basis"] = "explicit"
    assert interpret_requirements(item, raw)["interpretation"]["concepts"][0]["basis"] == "inferred"
    raw = payload()
    raw["interpretation"]["dependencies"] = ["invented framework"]
    with pytest.raises(ValueError):
        interpret_requirements(item, raw)


def test_empty_or_ambiguous_issues_can_remain_unknown():
    item = task()
    item.title, item.description = "Help", ""
    raw = payload()
    raw["interpretation"] = {"summary": None, "objective": None, "activities": [],
                             "concepts": [], "uncertainties": ["No task is described."]}
    fields = interpret_requirements(item, raw)
    assert fields["skills"] == [] and fields["difficulty"] is None
    assert fields["interpretation"]["summary"] is None
    raw["interpretation"] = None
    assert interpret_requirements(item, raw)["interpretation"] is None


def test_fabricated_stack_cannot_gain_matching_points_from_generic_quote():
    item = task()
    raw = payload()
    raw["skills"] = [{"skill": "kubernetes", "basis": "explicit", "rationale": "Maybe needed.", "source_quote": QUOTE}]
    fields = interpret_requirements(item, raw)
    assert fields["skills"] == []
    raw["skills"][0].update(skill="accessibility", basis="inferred")
    fields = interpret_requirements(item, raw)
    row = SimpleNamespace(model=MODEL, content_hash=fingerprint(item), fields=fields, updated_at=1)
    meta = effective_metadata(item, row)
    assert meta["skill_weights"] == {"accessibility": 0.5}
    assert score({"skills": ["accessibility"]}, meta, "test/map")[0] == 100
    # Concepts and summaries are never added to assessed skills or score factors.
    assert score({"skills": ["accessible navigation"]}, meta, "test/map")[0] == 0
    raw["skills"][0]["source_quote"] = None
    assert interpret_requirements(item, raw)["skills"] == []


def test_project_stack_inference_is_discounted_and_difficulty_requires_evidence():
    item = task()
    item.project = {"languages": ["javascript"]}
    raw = payload()
    raw["skills"] = [{"skill": "javascript", "basis": "explicit", "rationale": "Project stack plus focus work.", "source_quote": QUOTE}]
    raw.update(difficulty="Beginner", difficulty_reason="Seems easy")
    fields = interpret_requirements(item, raw)
    assert fields["evidence"][0]["basis"] == "inferred"
    assert fields["difficulty"] is None


def test_original_and_interpreted_search_without_live_ai(client, db_engine, monkeypatch):
    from app import enrichment
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(enrichment, "extract", lambda *a: pytest.fail("Browsing called AI"))
    ids = seed(db_engine)
    with Session(db_engine) as db:
        item = db.get(Task, ids[3])
        item.description = QUOTE
        db.add(IssueEnrichment(task_id=item.id, model=MODEL, content_hash=fingerprint(item),
                               fields={**interpret_requirements(item, payload()), "status": "accepted"}, updated_at=1))
        db.commit()
    register(client)
    def search(q):
        return client.get('/api/recommendations', params={"q": q}).json()
    assert search("keyboard")["items"][0]["search_match"] == "source"
    assert search("mouse")["items"][0]["search_match"] == "interpreted"
    found = search("navigation accessible")
    assert found["total"] == 1
    assert found["items"][0]["search_match"] == "inferred_concept"
    assert found["items"][0]["score"] is None
    assert found["items"][0]["metadata"]["skills"] == []
    assert search("acceptance criteria")["total"] == 0  # Missing facts are not search claims.
    assert search("navigation python")["total"] == 0
    assert search("%_")["total"] == 0
    assert search("  KEYBOARD  focus ")["total"] == 1
    assert search("Python transit")["total"] == 1  # Existing source search survives.
    with Session(db_engine) as db:
        db.get(Task, ids[3]).description = "Changed request"
        db.commit()
    assert search("accessible navigation")["total"] == 0
    assert "interpretation" not in client.get(f'/api/tasks/{ids[3]}').json()["metadata"]


def test_legacy_cache_retains_requirements_but_never_new_interpretation():
    item = task()
    row = SimpleNamespace(model=MODEL, content_hash=fingerprint(item, version=LEGACY_VERSION),
                          fields={"skills": ["javascript"], "evidence": [], "interpretation": interpretation()}, updated_at=1)
    assert cached_fields(item, row)["skills"] == ["javascript"]
    assert "interpretation" not in effective_metadata(item, row)
    assert row.content_hash != fingerprint(item)  # Explicit job can upgrade.
    item.description += " Source edit"
    assert cached_fields(item, row) == {}
    row.content_hash = fingerprint(item, version="unsupported-version")
    assert cached_fields(item, row) == {}


def test_malformed_or_rejected_cache_does_not_surface_interpretation():
    item = task()
    fields = {**interpret_requirements(item, payload()), "status": "rejected"}
    row = SimpleNamespace(model=MODEL, content_hash=fingerprint(item), fields=fields, updated_at=1)
    assert "interpretation" not in effective_metadata(item, row)
    fields["status"] = "accepted"
    fields["interpretation"]["summary"]["source_quote"] = "Missing quotation"
    assert "interpretation" not in effective_metadata(item, row)


def test_structured_snapshot_roundtrip_preserves_only_public_fields(db_engine, target, tmp_path):
    source_database(db_engine)
    with Session(db_engine) as db:
        item = db.get(Task, 5)
        item.description = QUOTE
        fields = interpret_requirements(item, payload())
        fields["status"] = "accepted"
        fields["interpretation"]["summary"]["private_account"] = "SECRET_SENTINEL"
        row = db.get(IssueEnrichment, item.id)
        row.fields = fields
        row.content_hash = fingerprint(item, project_context(PROJECT))
        db.commit()
    path = tmp_path / 'structured.json.gz'
    export_snapshot(path, db_engine)
    snapshot = load_snapshot(path)
    assert "SECRET_SENTINEL" not in snapshot.model_dump_json()
    assert import_snapshot(path, target)["imported_caches"] == 1
    from sqlalchemy import select
    with Session(target) as db:
        item = db.scalar(select(Task).where(Task.status == "open"))
        row = db.get(IssueEnrichment, item.id)
        assert effective_metadata(item, row, project=project_context(PROJECT))["interpretation"] == interpretation()


def test_bundled_v2_snapshot_remains_readable_without_reprocessing():
    snapshot = load_snapshot(DEFAULT_SNAPSHOT)  # Read-only; never import into a developer DB.
    issues = [issue for source in snapshot.sources for issue in source.issues]
    assert len(issues) == 21558
    assert sum(issue.enrichment is not None for issue in issues) == 2220
    for source in snapshot.sources:
        item = next(i for i in source.issues if i.enrichment is not None)
        cache = item.enrichment
        row = SimpleNamespace(model=cache.model, content_hash=cache.content_hash,
                              fields=cache.fields.model_dump(), updated_at=cache.updated_at)
        assert cached_fields(item, row, project_context(source.project.model_dump()))
        assert row.content_hash != fingerprint(item, project_context(source.project.model_dump()))


def test_explicit_job_upgrades_legacy_once_and_caches_structured_result(db_engine, monkeypatch):
    import json

    import httpx

    from app.enrichment import run
    ids = seed(db_engine)
    with Session(db_engine) as db:
        for tid in ids[:-1]:
            db.get(Task, tid).status = "closed"
        item = db.get(Task, ids[-1])
        item.description = QUOTE
        db.add(IssueEnrichment(task_id=item.id, model=MODEL,
                               content_hash=fingerprint(item, version=LEGACY_VERSION),
                               fields={"skills": [], "evidence": [], "status": "accepted"}, updated_at=1))
        db.commit()
    calls = []
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-test-key")
    def handler(request):
        sent = json.loads(request.content)
        assert sent["response_format"]["json_schema"]["name"] == "issue_interpretation"
        assert "interpretation" in sent["response_format"]["json_schema"]["schema"]["required"]
        calls.append(1)
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(payload())}}],
                                        "usage": {"prompt_tokens": 50, "completion_tokens": 100}})
    transport = httpx.MockTransport(handler)
    assert run(1, 0.001, db_engine, transport, workers=1)["enriched"] == 0
    assert calls == []
    assert run(1, 0.02, db_engine, transport, workers=1)["enriched"] == 1
    assert run(1, 0.02, db_engine, transport, workers=1)["enriched"] == 0
    assert calls == [1]
    with Session(db_engine) as db:
        item = db.get(Task, ids[-1])
        row = db.get(IssueEnrichment, item.id)
        assert cached_fields(item, row)["interpretation"] == interpretation()


def test_legacy_snapshot_import_keeps_old_cache_and_local_database_compatible(db_engine, target, tmp_path):
    import gzip
    import hashlib
    import json

    from app.enrichment_prompt_legacy import PROMPT_VERSION, SYSTEM_PROMPT
    from app.snapshot import canonical
    source_database(db_engine)
    with Session(db_engine) as db:
        item = db.get(Task, 5)
        row = db.get(IssueEnrichment, item.id)
        row.content_hash = fingerprint(item, project_context(PROJECT), version=LEGACY_VERSION)
        row.fields = {**row.fields, "prompt_version": PROMPT_VERSION}
        db.commit()
    path = tmp_path / 'legacy.json.gz'
    export_snapshot(path, db_engine)
    envelope = json.loads(gzip.decompress(path.read_bytes()))
    envelope['data'].update(extraction_version=LEGACY_VERSION, prompt_version=PROMPT_VERSION,
                            system_prompt=SYSTEM_PROMPT)
    envelope['sha256'] = hashlib.sha256(canonical(envelope['data'])).hexdigest()
    path.write_bytes(gzip.compress(canonical(envelope)))
    assert import_snapshot(path, target)["imported_caches"] == 1
    from sqlalchemy import select
    with Session(target) as db:
        item = db.scalar(select(Task).where(Task.status == "open"))
        row = db.get(IssueEnrichment, item.id)
        meta = effective_metadata(item, row, project=project_context(PROJECT))
        assert meta["skills"] == ["javascript"]
        assert "interpretation" not in meta
