"""Saved public research, matched by stable URL and unchanged source text."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def reviews():
    path = Path(__file__).resolve().parents[2] / "data" / "discovery-reviews.json"
    data = json.loads(path.read_text())
    return {
        item["url"]: {**item, "provenance": data["provenance"]}
        for item in data["issues"]
    }


def reviewed_context(task, research=None, project=None):
    item = reviews().get(getattr(task, "url", ""))
    text = " ".join((task.title + "\n" + task.description).split())
    if item and hashlib.sha256(text.encode()).hexdigest() == item["source_hash"]:
        return item
    from app.research_schema import research_review

    return research_review(task, research, project or {})


def add_reviewed_skills(task, metadata, correction=None, research=None, project=None):
    """Research suggestions remain inferred; curator skill edits take precedence."""
    review = reviewed_context(task, research, project)
    if not review or correction and "skills" in correction:
        return metadata
    result = dict(metadata)
    result["skills"] = list(metadata.get("skills", []))
    result["skill_weights"] = dict(metadata.get("skill_weights", {}))
    result["research_evidence"] = []
    source = " ".join((task.title + " " + task.description).casefold().split())
    for suggestion in review["skills"]:
        if " ".join(suggestion["quote"].casefold().split()) not in source:
            continue
        skill = suggestion["name"].strip().lower()
        if skill not in result["skills"]:
            result["skills"].append(skill)
            result["skill_weights"][skill] = 0.5
        result["research_evidence"].append(
            {
                "skill": skill,
                "rationale": suggestion["reason"],
                "quote": suggestion["quote"],
            }
        )
    return result
