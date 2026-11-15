"""Trial search semantics over current public metadata and source text."""

import re

SYNONYMS = [
    ["login", "signin", "authentication"],
    ["frontend", "frontend development"],
    ["backend", "backend development"],
    ["javascript", "js"],
    ["documentation", "docs"],
    ["api", "apis"],
    ["tile", "tiles"],
    ["report", "reports"],
    ["email", "emails"],
    ["ingredient", "ingredients"],
    ["map", "maps", "mapping"],
]


def normalize(value):
    text = re.sub(r"sign[ -]in", "signin", str(value).casefold())
    text = re.sub(r"front[ -]end", "frontend", text)
    text = re.sub(r"back[ -]end", "backend", text)
    return " ".join(
        word.strip(".")
        for word in re.sub(r"[^\w+#.]+|_", " ", text).split()
        if word.strip(".")
    )


def contains(text, term, expand=True):
    text = " " + normalize(text) + " "
    alternatives = (
        next((group for group in SYNONYMS if term in group), [term])
        if expand
        else [term]
    )
    return any(" " + word + " " in text for word in alternatives)


def skill_matches(value, selected):
    value, selected = normalize(value), normalize(selected)
    return value == selected or any(
        value in group and selected in group for group in SYNONYMS
    )


def search_result(task, meta, query, include_suggested=True, review=None, project=None):
    terms = normalize(query).split()
    if query.strip() and not terms:
        return None
    info = meta.get("interpretation") or {}
    recorded = [
        s
        for s in meta.get("skills", [])
        if meta.get("skill_weights", {}).get(s, 1) >= 1
    ]
    task_text = [task.title, *recorded]
    task_text += [
        info[key]["text"] for key in ["summary", "objective"] if info.get(key)
    ]
    task_text += [item["text"] for item in info.get("activities", [])]
    task_text += [
        item["text"] for item in info.get("concepts", []) if item["basis"] == "explicit"
    ]
    if review:
        task_text += [review[key] for key in ["summary", "purpose", "work"]]
    text = " ".join(task_text)
    levels = [("interpreted", text)]
    text += " " + task.description + " " + " ".join(task.labels)
    levels.append(("source", text))
    if include_suggested:
        text += " " + " ".join(meta.get("skills", []))
        levels.append(("suggested_skill", text))
        text += " " + " ".join(
            item["text"]
            for item in info.get("concepts", [])
            if item["basis"] == "inferred"
        )
        levels.append(("inferred_concept", text))
    project = project or {}
    text += " " + " ".join(
        [
            project.get("mission", ""),
            *meta.get("topics", []),
            review["background"] if review else "",
            review["project"] if review else "",
        ]
    )
    levels.append(("background", text))
    if not terms:
        return {"kind": "source", "rank": 0, "related_wording": False}
    for rank, (kind, text) in enumerate(levels):
        if all(contains(text, term) for term in terms):
            return {
                "kind": kind,
                "rank": rank,
                "related_wording": not all(
                    contains(text, term, False) for term in terms
                ),
            }
    return None
