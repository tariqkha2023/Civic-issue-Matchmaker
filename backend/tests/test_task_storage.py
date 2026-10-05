from app.connectors.models import RepositoryTask
from app.database import get_connection
from app.task_storage import (
    create_tasks_table,
    get_tasks,
    upsert_task,
    upsert_tasks,
)


def test_create_tasks_table():
    create_tasks_table()

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'tasks'
                ORDER BY ordinal_position;
                """
            )

            columns = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

    assert columns == [
        "id",
        "source",
        "source_id",
        "repository",
        "title",
        "description",
        "url",
        "status",
        "labels",
        "created_at",
        "updated_at",
    ]


def test_upsert_task_inserts_and_updates():
    create_tasks_table()

    task = RepositoryTask(
        source="github",
        source_id="999999",
        repository="example/project",
        title="Original title",
        description="Original description",
        url="https://example.com/issues/999999",
        status="open",
        labels=["backend"],
    )

    upsert_task(task)

    updated_task = RepositoryTask(
        source="github",
        source_id="999999",
        repository="example/project",
        title="Updated title",
        description="Updated description",
        url="https://example.com/issues/999999",
        status="closed",
        labels=["backend", "database"],
    )

    upsert_task(updated_task)

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT title, description, status, labels
                FROM tasks
                WHERE source = %s AND source_id = %s;
                """,
                ("github", "999999"),
            )

            row = cursor.fetchone()
    finally:
        conn.close()

    assert row == (
        "Updated title",
        "Updated description",
        "closed",
        ["backend", "database"],
    )


def test_upsert_tasks_stores_multiple_tasks():
    create_tasks_table()

    tasks = [
        RepositoryTask(
            source="github",
            source_id="1001",
            repository="example/github-project",
            title="GitHub task",
            description="Task from GitHub",
            url="https://example.com/github/1001",
            status="open",
            labels=["python"],
        ),
        RepositoryTask(
            source="gitlab",
            source_id="2001",
            repository="example/gitlab-project",
            title="GitLab task",
            description="Task from GitLab",
            url="https://example.com/gitlab/2001",
            status="opened",
            labels=["frontend"],
        ),
    ]

    upsert_tasks(tasks)

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT source, source_id, repository, title
                FROM tasks
                WHERE source_id IN (%s, %s)
                ORDER BY source;
                """,
                ("1001", "2001"),
            )

            rows = cursor.fetchall()
    finally:
        conn.close()

    assert rows == [
        (
            "github",
            "1001",
            "example/github-project",
            "GitHub task",
        ),
        (
            "gitlab",
            "2001",
            "example/gitlab-project",
            "GitLab task",
        ),
    ]


def test_get_tasks_returns_stored_tasks():
    create_tasks_table()

    task = RepositoryTask(
        source="github",
        source_id="4001",
        repository="example/read-project",
        title="Readable task",
        description="Task used to test retrieval",
        url="https://example.com/issues/4001",
        status="open",
        labels=["read"],
    )

    upsert_task(task)

    tasks = get_tasks()

    matching = [
        stored_task
        for stored_task in tasks
        if stored_task["source"] == "github"
        and stored_task["source_id"] == "4001"
    ]

    assert len(matching) == 1
    assert matching[0]["title"] == "Readable task"
    assert matching[0]["repository"] == "example/read-project"