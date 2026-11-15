from app.task_guidance import task_guidance


def test_task_questions_are_separate_from_internal_review_limitations():
    result = task_guidance(
        [
            "Confirm how a point belonging to several features should appear. This review did not inspect the attached screenshot.",
            "The linked wiki could not be retrieved. Confirm which country is in scope.",
            "The proposal names Ingredients.pm, but its implementation was not inspected.",
            "The error screenshot was not supplied by the author.",
        ]
    )
    assert result["questions"] == [
        "Confirm how a point belonging to several features should appear.",
        "Confirm which country is in scope.",
        "The error screenshot was not supplied by the author.",
    ]
    assert len(result["review_notes"]) == 3


def test_empty_notes_do_not_create_a_contributor_warning():
    assert task_guidance(["", " "]) == {"questions": [], "review_notes": []}
