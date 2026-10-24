"""Explicit, budget-limited OpenRouter enrichment of public issue text only.

No API calls occur during discovery. Cached results survive restarts and work
without a key. Curator corrections and explicit source labels take precedence.
"""

import argparse
import hashlib
import json
import os
import re
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from itertools import zip_longest
from types import SimpleNamespace

import httpx
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment_prompt import PROMPT_VERSION, SYSTEM_PROMPT, Requirements
from app.store import (
    EnrichmentRun,
    IssueEnrichment,
    Repository,
    SourceSettings,
    Task,
    engine,
)

MODEL = "deepseek/deepseek-v3.2"
VERSION = PROMPT_VERSION + "-production-v1"
INPUT_CEILING = 0.35
OUTPUT_CEILING = 0.60


class SkillEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill: str = Field(min_length=1, max_length=60)
    evidence: str = Field(min_length=3, max_length=300)


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skills: list[SkillEvidence] = Field(max_length=8)
    difficulty: str | None
    difficulty_evidence: str | None


def public_text(task):
    return (
        task.title + "\n" + task.description + "\nLabels: " + ", ".join(task.labels)
    )[:14000]


def fingerprint(task, project=None):
    return hashlib.sha256(
        (
            VERSION
            + MODEL
            + json.dumps(
                [
                    task.title,
                    task.description,
                    task.labels,
                    project if project is not None else getattr(task, "project", {}),
                ],
                ensure_ascii=False,
            )
        ).encode()
    ).hexdigest()


def cached_fields(task, row, project=None):
    if row is None or row.content_hash != fingerprint(task, project):
        return {}
    return row.fields


def effective_metadata(task, enrichment=None, correction=None, project=None):
    meta = dict(task.metadata_fields)
    fields = cached_fields(task, enrichment, project)
    if fields and fields.get("status") != "rejected":
        meta["skills"] = sorted(set(meta.get("skills", [])) | set(fields["skills"]))
        if not meta.get("difficulty") and fields.get("difficulty"):
            meta["difficulty"] = fields["difficulty"]
        meta["skill_weights"] = {skill: 1.0 for skill in meta["skills"]}
        for item in fields.get("evidence", []):
            if item["skill"] not in task.metadata_fields.get("skills", []):
                meta["skill_weights"][item["skill"]] = (
                    0.5 if item.get("basis") == "inferred" else 1.0
                )
        meta["ai_evidence"] = fields["evidence"]
        meta["ai_model"] = enrichment.model
        meta["ai_updated_at"] = enrichment.updated_at
    meta.update(correction or {})
    if correction and "skills" in correction:
        meta["skill_weights"] = {skill: 1.0 for skill in correction["skills"]}
    return meta


def validate_extraction(task, raw, *, check_evidence=True):
    result = Extraction.model_validate(raw)
    if not check_evidence:
        if result.difficulty not in [None, "Beginner", "Intermediate", "Advanced"]:
            raise ValueError("Invalid difficulty")
        evidence = {
            item.skill.strip().lower(): item.evidence
            for item in result.skills
            if item.skill.strip()
        }
        return {
            "skills": list(evidence),
            "evidence": [
                {"skill": skill, "quote": quote} for skill, quote in evidence.items()
            ],
            "difficulty": result.difficulty,
            "difficulty_evidence": result.difficulty_evidence,
        }
    source = public_text(task).casefold()

    def normalize(text):
        return " ".join(text.casefold().split())

    evidence = []
    for item in result.skills:
        # Reject invented quotations; these checks establish grounding, not truth.
        if normalize(item.evidence) not in normalize(source):
            raise ValueError("Skill evidence is not present in source text")
        skill = item.skill.strip().lower()
        explicit = {
            "python": r"\bpython\b|\.py\b|\bdjango\b|\bflask\b|\bfastapi\b",
            "javascript": r"\bjavascript\b|\bjs\b|\.js\b|\bjquery\b",
            "typescript": r"\btypescript\b|\bts\b|\.tsx?\b",
            "perl": r"\bperl\b|\.p[lm]\b|\bcpan\b",
            "react": r"\breact\b|\.jsx\b|\.tsx\b",
            "html": r"\bhtml\b|\.html\b",
            "css": r"\bcss\b|\bscss\b|\bstylesheet",
            "sql": r"\bsql\b|\bpostgres|\bmysql\b",
            "documentation": r"\bdocumentation\b|\bdocs?\b|\breadme\b|\buser guide\b",
            "testing": r"\btests?\b|\btesting\b|\bpytest\b|\bjest\b|\bunittest\b",
            "design": r"\bdesign\b|\bfigma\b|\bwireframe|\bmockup",
            "accessibility": r"\baccessibility\b|\ba11y\b|\bwcag\b|\bscreen reader",
            "frontend": r"\bfront[ -]?end\b",
            "backend": r"\bback[ -]?end\b",
            "devops": r"\bdevops\b|\bdeploy|\bci/cd\b|\bpipeline",
        }
        # A quote must support the named skill, not merely exist somewhere.
        if skill in {
            "id",
            "openstreetmap",
            "fixmystreet",
            "hackforla",
            "open food facts",
        }:
            continue
        anchor = explicit.get(skill, r"(?<!\w)" + re.escape(skill) + r"(?!\w)")
        if not re.search(anchor, item.evidence, re.I):
            continue
        if skill and skill not in [e["skill"] for e in evidence]:
            evidence.append({"skill": skill, "quote": item.evidence})
    difficulty = result.difficulty
    if difficulty not in [None, "Beginner", "Intermediate", "Advanced"]:
        raise ValueError("Invalid difficulty")
    if difficulty and (
        not result.difficulty_evidence
        or normalize(result.difficulty_evidence) not in normalize(source)
    ):
        raise ValueError("Difficulty requires a source quotation")
    if difficulty:
        anchors = {
            "Beginner": r"beginner|good first issue|new contributor|suitable for volunteers|easy",
            "Intermediate": r"intermediate",
            "Advanced": r"advanced|expert",
        }
        if not re.search(anchors[difficulty], result.difficulty_evidence, re.I):
            difficulty = None
    return {
        "skills": [e["skill"] for e in evidence],
        "evidence": evidence,
        "difficulty": difficulty,
        "difficulty_evidence": result.difficulty_evidence if difficulty else None,
    }


def interpret_requirements(task, raw):
    result = Requirements.model_validate(raw)
    source = " ".join(public_text(task).casefold().split())
    evidence = {}
    for item in result.skills:
        skill = item.skill.strip().lower()
        if not skill:
            continue
        quote = item.source_quote
        quote_matches = bool(quote and " ".join(quote.casefold().split()) in source)
        # Never drop inferred skills for lacking literal keywords/quotations.
        # An unsupported "explicit" claim is retained, labeled as inference.
        basis = item.basis if item.basis == "inferred" or quote_matches else "inferred"
        entry = {
            "skill": skill,
            "basis": basis,
            "rationale": item.rationale,
            "quote": quote if quote_matches else None,
        }
        if skill not in evidence or basis == "explicit":
            evidence[skill] = entry
    return {
        "skills": list(evidence),
        "evidence": list(evidence.values()),
        "difficulty": result.difficulty,
        "difficulty_evidence": result.difficulty_reason,
        "prompt_version": PROMPT_VERSION,
    }


def project_context(fields):
    return {key: fields.get(key) for key in ["name", "mission", "languages", "topics"]}


def extract(task, key, client):
    response = client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "X-Title": "Civic Issue Matchmaker"},
        json={
            "model": MODEL,
            "max_tokens": 1800,
            "temperature": 0,
            "provider": {
                "require_parameters": True,
                "sort": "latency",
                "max_price": {"prompt": INPUT_CEILING, "completion": OUTPUT_CEILING},
            },
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "minimal_requirements",
                    "strict": True,
                    "schema": Requirements.model_json_schema(),
                },
            },
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "project": getattr(task, "project", {}),
                            "issue": public_text(task),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        },
    )
    if response.status_code != 200:
        # Never echo upstream bodies, headers, or request objects containing credentials.
        raise RuntimeError(
            f"OpenRouter HTTP {response.status_code}; stopped without retry"
        )
    data = response.json()
    usage = data.get("usage", {})
    # Conservative provider ceilings; actual cost is used when supplied.
    estimate = (
        usage.get("prompt_tokens", 0) * INPUT_CEILING / 1e6
        + usage.get("completion_tokens", 1800) * OUTPUT_CEILING / 1e6
    )
    cost = max(float(usage.get("cost") or 0), estimate)
    content = data["choices"][0]["message"].get("content")
    return content or "{}", cost


def request_reserve(task):
    # UTF-8 bytes upper-bound input tokens conservatively; add room for schema,
    # instructions, and chat framing. Output is bounded by max_tokens.
    return (
        (
            len(public_text(task).encode())
            + len(json.dumps(getattr(task, "project", {})).encode())
            + 9000
        )
        * INPUT_CEILING
        + 1800 * OUTPUT_CEILING
    ) / 1e6


def run(limit=50, budget=0.25, db_engine=engine, transport=None, workers=4):
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY in backend/.env")
    from app.github_sync import acquire, release
    from app.migrations import migrate
    from app.store import JobLease

    migrate(db_engine)
    count, failed, spent = 0, 0, 0.0
    with (
        Session(db_engine) as db,
        httpx.Client(timeout=60, transport=transport) as client,
    ):
        if not acquire(db, "issue-enrichment"):
            raise RuntimeError("Another enrichment job is running")
        ledger = EnrichmentRun(
            fields={
                "model": MODEL,
                "started_at": time.time(),
                "status": "running",
                "budget": budget,
            }
        )
        db.add(ledger)
        db.commit()
        error = False
        try:
            groups = {}
            cached = {row.task_id: row for row in db.scalars(select(IssueEnrichment))}
            projects = {
                row.repository_id: project_context(row.fields)
                for row in db.scalars(select(SourceSettings))
            }
            for task in db.scalars(
                select(Task)
                .join(Repository)
                .where(
                    Task.status == "open",
                    Repository.source == "github",
                    Repository.enabled.is_(True),
                )
                .order_by(Task.id.desc())
            ):
                row = cached.get(task.id)
                if row and row.content_hash == fingerprint(
                    task, projects.get(task.repository_id, {})
                ):
                    continue
                # Threads receive detached plain public data, never ORM sessions/accounts.
                public = SimpleNamespace(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    labels=task.labels,
                    project=projects.get(task.repository_id, {}),
                )
                groups.setdefault(task.repository_id, []).append(public)
            pending_tasks = iter(
                t
                for batch in zip_longest(*groups.values())
                for t in batch
                if t is not None
            )
            active, reserved, submitted = {}, 0.0, 0
            exhausted = False
            with ThreadPoolExecutor(max_workers=workers) as pool:
                while active or not exhausted:
                    while not exhausted and len(active) < workers and submitted < limit:
                        task = next(pending_tasks, None)
                        if task is None:
                            exhausted = True
                            break
                        reserve = request_reserve(task)
                        if spent + reserved + reserve > budget:
                            # Finish outstanding requests before deciding whether more fit.
                            if active:
                                pending_tasks = iter([task, *pending_tasks])
                            else:
                                exhausted = True
                            break
                        active[pool.submit(extract, task, key, client)] = (
                            task,
                            reserve,
                        )
                        reserved += reserve
                        submitted += 1
                    if submitted >= limit:
                        exhausted = True
                    if not active:
                        break
                    ready, _ = wait(active, return_when=FIRST_COMPLETED)
                    for future in ready:
                        task, reserve = active.pop(future)
                        reserved -= reserve
                        try:
                            raw, cost = future.result()
                        except (RuntimeError, ValueError, httpx.HTTPError, KeyError):
                            failed += 1
                            spent += reserve  # Ambiguous failures may still be billed.
                            error = True
                            exhausted = True
                            print(
                                f"Issue {task.id}: provider unavailable; stopping new requests",
                                flush=True,
                            )
                        else:
                            spent += cost
                            try:
                                fields = interpret_requirements(task, json.loads(raw))
                            except ValueError:
                                fields = {
                                    "status": "rejected",
                                    "skills": [],
                                    "evidence": [],
                                    "difficulty": None,
                                    "difficulty_evidence": None,
                                }
                                failed += 1
                            else:
                                fields["status"] = "accepted"
                                count += 1
                            # Source may have changed while the request was in flight.
                            source = db.get(Task, task.id, populate_existing=True)
                            current_settings = db.get(
                                SourceSettings,
                                source.repository_id,
                                populate_existing=True,
                            )
                            current_project = (
                                project_context(current_settings.fields)
                                if current_settings
                                else {}
                            )
                            if fingerprint(source, current_project) == fingerprint(
                                task
                            ):
                                row = db.get(IssueEnrichment, task.id)
                                if row is None:
                                    row = IssueEnrichment(task_id=task.id)
                                    db.add(row)
                                row.content_hash, row.model, row.fields = (
                                    fingerprint(task),
                                    MODEL,
                                    fields,
                                )
                                row.cost, row.updated_at = cost, time.time()
                                print(
                                    f"Issue {task.id}: {', '.join(fields['skills']) or fields['status'] + ' / insufficient evidence'}; budget used ${spent:.4f}",
                                    flush=True,
                                )
                            else:
                                failed += 1
                        ledger.fields = {
                            **ledger.fields,
                            "enriched": count,
                            "rejected": failed,
                            "cost_upper_estimate": round(spent, 6),
                        }
                        db.get(JobLease, "issue-enrichment").expires_at = (
                            time.time() + 900
                        )
                        db.commit()
        finally:
            ledger.fields = {
                **ledger.fields,
                "status": "provider_error" if error else "finished",
                "finished_at": time.time(),
            }
            db.commit()
            release(db, "issue-enrichment")
    return {
        "enriched": count,
        "rejected": failed,
        "cost_upper_estimate": round(spent, 6),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--budget", type=float, default=0.25)
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9))
    args = parser.parse_args()
    if not 1 <= args.limit <= 10000 or not 0.001 <= args.budget <= 2:
        parser.error("Use limit 1..10000 and budget $0.001..$2")
    try:
        print(json.dumps(run(args.limit, args.budget, workers=args.workers)))
    except (RuntimeError, ValueError, httpx.HTTPError, KeyError):
        raise SystemExit(
            "Enrichment stopped; saved results preserved. Check key, provider availability, and budget."
        )
