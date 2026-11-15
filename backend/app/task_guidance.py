"""Separate actionable task questions from limitations of an internal review."""

import re

REVIEW_LANGUAGE = re.compile(
    r"\b(?:this|our|the) review\b|\bduring review\b|\breviewer\b|"
    r"\b(?:was|were|not|never) (?:not )?(?:inspected|reviewed|retrieved|verified)\b|"
    r"\bcould not (?:be )?(?:retrieve|access|inspect|verify)\w*\b|"
    r"\b(?:wiki|links?) (?:denied access|could not)\b|"
    r"\bno (?:migration|verification|inspection) was performed\b|"
    r"\b(?:AI|model|prompt|schema|inference|extraction)\b",
    re.I,
)


def task_guidance(uncertainties):
    questions, review_notes = [], []
    for statement in uncertainties:
        # Classify clauses separately so useful task questions survive a sentence
        # that also mentions an uninspected screenshot or inaccessible wiki.
        for sentence in re.split(r"(?<=[.!?;])\s+", statement):
            sentence = sentence.strip()
            if not sentence:
                continue
            target = review_notes if REVIEW_LANGUAGE.search(sentence) else questions
            if sentence not in target:
                target.append(sentence)
    return {"questions": questions, "review_notes": review_notes}
