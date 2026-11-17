"""Explicit research jobs for the real Discover API. Collection never calls AI."""

import argparse
import json
import math
import os
import time
from itertools import zip_longest

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.discovery_context import reviewed_context
from app.enrichment import (
    INPUT_CEILING,
    MAX_OUTPUT_TOKENS,
    MODEL,
    OUTPUT_CEILING,
    extract,
    project_context,
)
from app.github_sync import acquire, release
from app.migrations import migrate
from app.research_collect import CollectionError, Collector
from app.research_schema import (
    SYSTEM_PROMPT,
    VERSION,
    ResearchResult,
    digest,
    source_hash,
    validate_result,
)
from app.store import (
    IssueResearch,
    JobLease,
    Repository,
    ResearchRun,
    SourceSettings,
    Task,
    engine,
)


def reservation(bundle):
    return (
        (
            len(json.dumps(bundle).encode())
            + len(SYSTEM_PROMPT.encode())
            + len(json.dumps(ResearchResult.model_json_schema()).encode())
            + 2000
        )
        * INPUT_CEILING
        + MAX_OUTPUT_TOKENS * OUTPUT_CEILING
    ) / 1e6


def run(
    mode,
    limit=20,
    budget=0,
    task_ids=None,
    refresh=False,
    db_engine=engine,
    transport=None,
):
    if mode not in {"collect", "interpret"} or not 1 <= limit <= 100:
        raise ValueError("Use collect/interpret with limit 1..100")
    if mode == "interpret" and (not math.isfinite(budget) or not 0.001 <= budget <= 2):
        raise ValueError("Interpretation requires an explicit budget of $0.001..$2")
    key = os.getenv("OPENROUTER_API_KEY", "").strip() if mode == "interpret" else ""
    if mode == "interpret" and not key:
        raise ValueError(
            "Set OPENROUTER_API_KEY before explicitly running interpretation"
        )
    migrate(db_engine)
    stats = {
        "mode": mode,
        "attempted": 0,
        "collected": 0,
        "accepted": 0,
        "rejected": 0,
        "skipped": 0,
        "cost_upper_estimate": 0.0,
    }
    with (
        Session(db_engine) as db,
        httpx.Client(timeout=30, transport=transport, trust_env=False) as client,
    ):
        if not acquire(db, "context-research"):
            raise RuntimeError("Another research job is running")
        ledger = ResearchRun(
            fields={
                "kind": "context_research",
                "version": VERSION,
                "started_at": time.time(),
                "status": "running",
                "budget": budget,
            }
        )
        db.add(ledger)
        db.commit()
        status = "finished"
        try:
            stmt = (
                select(Task, Repository)
                .join(Repository)
                .where(
                    Repository.source == "github",
                    Repository.enabled.is_(True),
                    Task.status == "open",
                )
                .order_by(Task.id.desc())
            )
            if task_ids:
                stmt = stmt.where(Task.id.in_(task_ids))
            groups = {}
            for task, repo in db.execute(stmt):
                if not task_ids and reviewed_context(task):
                    stats["skipped"] += 1
                    continue
                groups.setdefault(repo.id, []).append((task, repo))
            collector = Collector(db, client, refresh)
            for group in zip_longest(*groups.values()):
                for pair in group:
                    if pair is None:
                        continue
                    task, repo = pair
                    settings = db.get(SourceSettings, repo.id)
                    project = project_context(settings.fields) if settings else {}
                    row = db.get(IssueResearch, task.id)
                    data = row.fields if row else {}
                    bundle = data.get("bundle", {})
                    fresh = (
                        bundle.get("version") == VERSION
                        and bundle.get("source_hash") == source_hash(task, project)
                        and bundle.get("expires_at", 0) > time.time()
                    )
                    if mode == "collect" and fresh and not refresh:
                        stats["skipped"] += 1
                        continue
                    if mode == "interpret" and (
                        not fresh
                        or (
                            data.get("attempt_hash") == digest(bundle)
                            and data.get("model") == MODEL
                        )
                    ):
                        stats["skipped"] += 1
                        continue
                    if stats["attempted"] >= limit:
                        break
                    reserve = reservation(bundle) if mode == "interpret" else 0
                    if (
                        stats["cost_upper_estimate"] + reserve > budget
                        and mode == "interpret"
                    ):
                        status = "budget_limit"
                        break
                    stats["attempted"] += 1
                    if mode == "collect":
                        try:
                            bundle = collector.collect(task, repo.path, project)
                        except (
                            CollectionError,
                            httpx.HTTPError,
                            ValueError,
                            TypeError,
                            KeyError,
                        ):
                            stats["rejected"] += 1
                            continue
                        if row is None:
                            row = IssueResearch(task_id=task.id)
                            db.add(row)
                        # Keep the old result for audit, but its hash no longer matches.
                        row.fields = {
                            **data,
                            "bundle": bundle,
                            "collection_status": "collected",
                        }
                        stats["collected"] += 1
                    else:
                        # Reserve the full conservative ceiling, including ambiguous failures.
                        stats["cost_upper_estimate"] += reserve
                        ledger.fields = {**ledger.fields, **stats}
                        db.commit()
                        try:
                            raw, _cost = extract(
                                task, key, client, research_bundle=bundle
                            )
                        except (RuntimeError, ValueError, httpx.HTTPError, KeyError):
                            status = "provider_error"
                            break
                        try:
                            result = validate_result(json.loads(raw), bundle)
                        except (ValueError, TypeError, KeyError):
                            row.fields = {
                                **data,
                                "attempt_hash": digest(bundle),
                                "status": "rejected",
                                "model": MODEL,
                            }
                            stats["rejected"] += 1
                        else:
                            # Reject a result if the source changed while waiting for the provider.
                            db.refresh(task)
                            if settings:
                                db.refresh(settings)
                            current_project = (
                                project_context(settings.fields) if settings else {}
                            )
                            if bundle["source_hash"] != source_hash(
                                task, current_project
                            ):
                                stats["rejected"] += 1
                                continue
                            row.fields = {
                                **data,
                                "result": result,
                                "result_hash": digest(bundle),
                                "attempt_hash": digest(bundle),
                                "status": "accepted",
                                "model": MODEL,
                                "generated_at": time.time(),
                            }
                            stats["accepted"] += 1
                    ledger.fields = {**ledger.fields, **stats}
                    db.get(JobLease, "context-research").expires_at = time.time() + 900
                    db.commit()
                    print(f"Issue {task.id}: {mode} saved", flush=True)
                if stats["attempted"] >= limit or status != "finished":
                    break
        except Exception:
            status = "failed"
            raise
        finally:
            db.rollback()
            ledger = db.get(ResearchRun, ledger.id)
            ledger.fields = {
                **ledger.fields,
                **stats,
                "status": status,
                "finished_at": time.time(),
            }
            db.commit()
            release(db, "context-research")
    return {**stats, "status": status}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["collect", "interpret"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--task-id", type=int, action="append")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh source collection and permit a new interpretation",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=0,
        help="Required for paid interpretation; maximum $2",
    )
    args = parser.parse_args()
    if args.refresh and args.mode != "collect":
        parser.error("Use --refresh with collect before retrying interpretation")
    try:
        print(
            json.dumps(
                run(args.mode, args.limit, args.budget, args.task_id, args.refresh)
            )
        )
    except (RuntimeError, ValueError, httpx.HTTPError):
        raise SystemExit(
            "Research stopped. Check mode, budget, provider availability and key configuration. Saved results are preserved."
        )


if __name__ == "__main__":
    main()
