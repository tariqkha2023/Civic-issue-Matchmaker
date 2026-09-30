"""Transparent scoring; unknown metadata is omitted rather than invented."""

import re

SKILLS = [
    "python",
    "react",
    "javascript",
    "typescript",
    "html",
    "css",
    "sql",
    "documentation",
    "accessibility",
    "design",
    "java",
    "go",
    "rust",
]
LEVELS = ["Beginner", "Intermediate", "Advanced"]


def derive_metadata(labels):
    lowered = [label.lower().strip() for label in labels]
    skills = [
        skill for skill in SKILLS if skill in lowered or f"skill:{skill}" in lowered
    ]
    difficulty = None
    if "good first issue" in lowered or "beginner" in lowered:
        difficulty = "Beginner"
    for level in LEVELS:
        if level.lower() in lowered or f"difficulty:{level.lower()}" in lowered:
            difficulty = level
    effort = next(
        (
            float(m.group(1))
            for label in lowered
            if (m := re.fullmatch(r"effort:(\d+(?:\.\d+)?)h", label))
        ),
        None,
    )
    topics = [
        label.split(":", 1)[1].strip()
        for label in labels
        if label.lower().startswith("topic:")
    ]
    return {
        "skills": skills,
        "topics": topics,
        "difficulty": difficulty,
        "effort": effort,
        "provenance": "Derived from repository labels; unspecified fields remain unknown.",
    }


def score(profile, metadata, repository):
    factors = []
    skills = {s.lower() for s in profile.get("skills", [])}
    interests = {s.lower() for s in profile.get("interests", [])}
    required = set(metadata["skills"])
    if required:
        fit = len(skills & required) / len(required)
        factors.append(
            (
                0.35,
                fit,
                f"Skills: {len(skills & required)} of {len(required)} required skills match.",
            )
        )
    if metadata["topics"]:
        fit = len(interests & {s.lower() for s in metadata["topics"]}) / len(
            metadata["topics"]
        )
        factors.append(
            (
                0.20,
                fit,
                "Interests align with this topic."
                if fit
                else "This topic is outside your listed interests.",
            )
        )
    if metadata["difficulty"]:
        task_level = LEVELS.index(metadata["difficulty"])
        experience = LEVELS.index(profile.get("level", "Beginner"))
        preference = LEVELS.index(profile.get("difficulty", "Beginner"))
        fit = (
            max(0, 1 - max(0, task_level - experience) / 2)
            + max(0, 1 - abs(task_level - preference) / 2)
        ) / 2
        factors.append(
            (
                0.15,
                fit,
                f"Difficulty is {metadata['difficulty']}; your experience is {LEVELS[experience]} and preference is {LEVELS[preference]}.",
            )
        )
    if metadata["effort"] is not None:
        effort = metadata["effort"]
        hours = profile.get("hours", 0)
        fit = min(1, hours / effort) if effort else 1
        factors.append(
            (
                0.15,
                fit,
                f"Estimated effort: {effort:g} hours; your availability: {hours:g} hours/week.",
            )
        )
    if profile.get("repositories"):
        fit = float(repository.lower() in profile["repositories"])
        factors.append(
            (
                0.05,
                fit,
                "Matches a preferred repository."
                if fit
                else "Outside your preferred repositories.",
            )
        )
    total = sum(w for w, _, _ in factors)
    result = (
        round(100 * sum(w * value for w, value, _ in factors) / total, 1)
        if total
        else None
    )
    explanations = [message for _, _, message in factors]
    if len(explanations) < 2:
        explanations.extend(
            [
                "Missing task metadata limits confidence in this recommendation.",
                "Only supplied or label-derived metadata contributes to the score.",
            ][: 2 - len(explanations)]
        )
    return result, explanations
