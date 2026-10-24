"""Read-only comparison: apply strict and unchecked parsing to identical AI replies.

Writes a local report, never production issue metadata. Costs at most the
conservative reservations for the selected requests; at most 20 issues.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment import (
    MODEL,
    cached_fields,
    extract,
    public_text,
    request_reserve,
    validate_extraction,
)
from app.store import IssueEnrichment, Repository, Task, engine


def trial():
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise SystemExit("OpenRouter key is not configured")
    selected, reservation = [], 0.0
    with Session(engine) as db:
        cached = {r.task_id: r for r in db.scalars(select(IssueEnrichment))}
        for repo in db.scalars(
            select(Repository)
            .where(Repository.source == "github", Repository.enabled.is_(True))
            .order_by(Repository.path)
        ):
            groups = {}
            for task in db.scalars(
                select(Task)
                .where(Task.repository_id == repo.id, Task.status == "open")
                .order_by(Task.id.desc())
            ):
                fields = cached_fields(task, cached.get(task.id))
                group = (
                    "not_processed"
                    if not fields
                    else "rejected"
                    if fields.get("status") == "rejected"
                    else "with_skills"
                    if fields.get("skills")
                    else "without_skills"
                )
                groups.setdefault(group, task)
            for group in ["rejected", "without_skills", "with_skills", "not_processed"]:
                task = groups.get(group)
                if task is None or reservation + request_reserve(task) > 0.10:
                    continue
                reservation += request_reserve(task)
                selected.append(
                    {
                        "id": task.id,
                        "repository": repo.path,
                        "title": task.title,
                        "description": task.description,
                        "labels": task.labels,
                        "url": task.url,
                        "sample_group": group,
                    }
                )
    from types import SimpleNamespace

    with httpx.Client(timeout=60) as client:

        def compare(item):
            task = SimpleNamespace(**item)
            result = {**item, "input": public_text(task)}
            try:
                text, cost = extract(task, key, client)
            except (RuntimeError, ValueError, httpx.HTTPError, KeyError):
                return {
                    **result,
                    "error": "provider_error",
                    "cost_upper_estimate": request_reserve(task),
                }
            result["cost_upper_estimate"] = cost
            result["raw_response"] = text
            try:
                raw = json.loads(text)
                result["unchecked"] = validate_extraction(
                    task, raw, check_evidence=False
                )
            except ValueError:
                return {**result, "error": "invalid_structure"}
            try:
                result["strict"] = validate_extraction(task, raw)
            except ValueError:
                result["strict"] = {"skills": [], "status": "rejected"}
            return result

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(compare, selected))
    summary = {
        "model": MODEL,
        "sample_size": len(results),
        "sampling": "Up to one rejected, empty, skill-bearing and unprocessed issue per repository; purposive comparison, not a random accuracy estimate.",
        "strict_with_skills": sum(
            bool(r.get("strict", {}).get("skills")) for r in results
        ),
        "unchecked_with_skills": sum(
            bool(r.get("unchecked", {}).get("skills")) for r in results
        ),
        "invalid_structure_or_provider_errors": sum(
            bool(r.get("error")) for r in results
        ),
        "cost_upper_estimate": round(sum(r["cost_upper_estimate"] for r in results), 6),
        "budget_reservation": round(reservation, 6),
        "production_data_changed": False,
    }
    path = (
        Path(__file__).resolve().parents[2]
        / ".local-tools"
        / "enrichment-comparison.json"
    )
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"summary": summary, "issues": results}, indent=2))
    print(json.dumps(summary, indent=2))
    print("Report:", path)


if __name__ == "__main__":
    trial()
