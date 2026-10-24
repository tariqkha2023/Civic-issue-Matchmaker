"""Compare a revised prompt on the same saved public-issue sample; no DB writes."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment import INPUT_CEILING, MODEL, OUTPUT_CEILING
from app.enrichment_prompt import PROMPT_VERSION, SYSTEM_PROMPT, Requirements
from app.store import Repository, SourceSettings, engine


def trial():
    root = Path(__file__).resolve().parents[2] / ".local-tools"
    old = json.loads((root / "enrichment-comparison.json").read_text())
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise SystemExit("OpenRouter key not configured")
    with Session(engine) as db:
        projects = {}
        for repo in db.scalars(select(Repository).where(Repository.source == "github")):
            settings = db.get(SourceSettings, repo.id)
            fields = settings.fields if settings else {}
            projects[repo.path] = {
                k: fields.get(k) for k in ["name", "mission", "languages", "topics"]
            }
    payloads, reserved = [], 0.0
    for item in old["issues"]:
        payload = {
            "model": MODEL,
            "temperature": 0,
            "max_tokens": 1800,
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
                            "project": projects.get(item["repository"], {}),
                            "issue": item["input"],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        reserve = (
            (len(json.dumps(payload).encode()) + 3000) * INPUT_CEILING
            + 1800 * OUTPUT_CEILING
        ) / 1e6
        if reserved + reserve > 0.10:
            raise SystemExit(
                "Sample exceeds ten-cent conservative reservation; no requests sent"
            )
        reserved += reserve
        payloads.append((item, payload, reserve))
    with httpx.Client(timeout=90) as client:

        def evaluate(args):
            item, payload, reserve = args
            result = {k: item[k] for k in ["id", "repository", "title", "url", "input"]}
            result["old_strict_skills"] = item.get("strict", {}).get("skills", [])
            result["old_unchecked_skills"] = item.get("unchecked", {}).get("skills", [])
            try:
                response = client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": "Bearer " + key},
                    json=payload,
                )
                if response.status_code != 200:
                    raise ValueError("Provider error")
                data = response.json()
                usage = data.get("usage", {})
                result["cost_upper_estimate"] = max(
                    float(usage.get("cost") or 0),
                    (
                        usage.get("prompt_tokens", 0) * INPUT_CEILING
                        + usage.get("completion_tokens", 1800) * OUTPUT_CEILING
                    )
                    / 1e6,
                )
                raw = data["choices"][0]["message"].get("content") or "{}"
                result["raw_response"] = raw
                parsed = Requirements.model_validate_json(raw).model_dump()
                # Report quotation fidelity, without discarding inferred requirements.
                source = " ".join(item["input"].casefold().split())
                for skill in parsed["skills"]:
                    quote = skill["source_quote"]
                    skill["quote_matches_source"] = (
                        (" ".join(quote.casefold().split()) in source)
                        if quote
                        else None
                    )
                result["revised"] = parsed
            except (ValueError, KeyError, httpx.HTTPError):
                result["error"] = "invalid_structure_or_provider_error"
                result.setdefault("cost_upper_estimate", reserve)
            return result

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(evaluate, payloads))
    summary = {
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "sample_size": len(results),
        "old_strict_with_skills": sum(bool(i["old_strict_skills"]) for i in results),
        "old_unchecked_with_skills": sum(
            bool(i["old_unchecked_skills"]) for i in results
        ),
        "revised_with_skills": sum(
            bool(i.get("revised", {}).get("skills")) for i in results
        ),
        "revised_explicit_skills": sum(
            s["basis"] == "explicit"
            for i in results
            for s in i.get("revised", {}).get("skills", [])
        ),
        "revised_inferred_skills": sum(
            s["basis"] == "inferred"
            for i in results
            for s in i.get("revised", {}).get("skills", [])
        ),
        "errors": sum(bool(i.get("error")) for i in results),
        "cost_upper_estimate": round(sum(i["cost_upper_estimate"] for i in results), 6),
        "budget_reservation": round(reserved, 6),
        "production_data_changed": False,
        "caveat": "Purposive development sample, not an independent accuracy evaluation; prompt and project context both changed.",
    }
    path = root / "enrichment-prompt-comparison.json"
    path.write_text(json.dumps({"summary": summary, "issues": results}, indent=2))
    print(json.dumps(summary, indent=2))
    print("Report:", path)


if __name__ == "__main__":
    trial()
