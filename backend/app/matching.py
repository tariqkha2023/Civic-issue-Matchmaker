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
SCORE_VERSION = "skills-interests-v5"
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
        factors.append(
            (
                0.80,
                fit,
                f"Skills: {len(skills & required)} of {len(required)} assessed skills match.",
            )
        )
    inferred = [s for s in required if metadata.get("skill_weights", {}).get(s, 1) < 1]
    if metadata["topics"] and interests:
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
    if repository.lower() in profile.get("repositories", []):
        preference = "Preferred repository; used to break equal-score ties, not inflate technical fit."
    else:
        preference = None
    total = sum(w for w, _, _ in factors)
    result = (
        round(100 * sum(w * value for w, value, _ in factors) / total, 1) if total else None
    )
    explanations = [message for _, _, message in factors]
    explanations.append(
        "Match score compares available skills and civic interests (80/20 when both are known). Unknown factors are omitted and remaining weights rescaled. Evidence strength is reported separately; this is not a probability of success."
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


def evidence_strength(metadata):
    """Evidence availability, not calibrated confidence or task completeness."""
    skills = set(metadata.get("skills", []))
    weights = metadata.get("skill_weights", {})
    reliability = sum(weights.get(s, 1) for s in skills) / len(skills) if skills else 0
    return round(80 * reliability + (20 if metadata.get("topics") else 0))
