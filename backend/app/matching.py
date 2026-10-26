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
    "perl",
    "ruby",
    "testing",
    "translation",
    "docker",
    "devops",
    "postgresql",
    "fastapi",
]
SCORE_VERSION = "evidence-v4"
LEVELS = ["Beginner", "Intermediate", "Advanced"]


def derive_metadata(labels):
    lowered = [label.lower().strip() for label in labels]
    skills = [
        skill for skill in SKILLS if skill in lowered or f"skill:{skill}" in lowered
    ]
    difficulty = None
    if any(
        label in lowered
        for label in [
            "good first issue",
            "beginner",
            "new contributor opportunity",
            "suitable for volunteers",
        ]
    ):
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


def score(profile, metadata, repository, history=None):
    factors = []
    if not metadata.get("skills") or not profile.get("skills"):
        return None, [
            "Limited information: issue-specific skills and your profile skills are needed for a fit score.",
            "Topic or repository preference alone does not establish technical fit.",
        ]
    skills = {s.lower() for s in profile.get("skills", [])}
    interests = {s.lower() for s in profile.get("interests", [])}
    required = set(metadata["skills"])
    if required:
        weights = {s: metadata.get("skill_weights", {}).get(s, 1.0) for s in required}
        total_skill_weight = sum(weights.values())
        fit = sum(weights[s] for s in skills & required) / total_skill_weight
        reliability = total_skill_weight / len(required)
        factors.append(
            (
                0.60 * reliability,
                fit,
                f"Skills: {len(skills & required)} of {len(required)} assessed skills match.",
            )
        )
    inferred = [s for s in required if metadata.get("skill_weights", {}).get(s, 1) < 1]
    if metadata["topics"]:
        fit = len(interests & {s.lower() for s in metadata["topics"]}) / len(
            metadata["topics"]
        )
        factors.append(
            (
                0.15,
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
                0.20,
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
                0.05,
                fit,
                f"Estimated effort: {effort:g} hours; your availability: {hours:g} hours/week.",
            )
        )
    if repository.lower() in profile.get("repositories", []):
        preference = "Preferred repository; used to break equal-score ties, not inflate technical fit."
    else:
        preference = None
    total = sum(w for w, _, _ in factors)
    result = (
        round(100 * sum(w * value for w, value, _ in factors), 1) if total else None
    )
    explanations = [message for _, _, message in factors]
    explanations.append(
        f"Evidence-backed score out of 100; available evidence supports at most {100 * total:g} points. Unassessed factors remain unknown."
    )
    if inferred:
        explanations.append(
            "AI-inferred skills carry half the evidence weight of stated or curator-reviewed skills: "
            + ", ".join(sorted(inferred))
            + "."
        )
    missing = sorted(required - skills)
    if missing:
        explanations.append(
            "Skills not listed in your profile: " + ", ".join(missing) + "."
        )
    if preference:
        explanations.append(preference)
    if history and history.get("relevance") is not None:
        explanations.append(
            "Your relevance feedback helps break equal-score ties; it does not change assessed skill fit."
        )
    if history and history.get("completed"):
        explanations.append(
            "Your completed activity helps break equal-score ties; completion is self-reported."
        )
    if len(explanations) < 2:
        explanations.extend(
            [
                "Missing task metadata limits confidence in this recommendation.",
                "Only source, validated AI, or curator-supplied requirements contribute to the score.",
            ][: 2 - len(explanations)]
        )
    return result, explanations
