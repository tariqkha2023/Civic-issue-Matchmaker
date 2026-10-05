from app.connectors.models import RepositoryTask
from app.database import get_connection


CREATE_TASKS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    repository TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    status TEXT NOT NULL,
    labels TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_tasks_source_source_id
        UNIQUE (source, source_id)
);
"""


def create_tasks_table():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_TASKS_TABLE_SQL)

        conn.commit()
    finally:
        conn.close()


def upsert_task(task: RepositoryTask):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (
                    source,
                    source_id,
                    repository,
                    title,
                    description,
                    url,
                    status,
                    labels
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, source_id)
                DO UPDATE SET
                    repository = EXCLUDED.repository,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    url = EXCLUDED.url,
                    status = EXCLUDED.status,
                    labels = EXCLUDED.labels,
                    updated_at = NOW();
                """,
                (
                    task.source,
                    task.source_id,
                    task.repository,
                    task.title,
                    task.description,
                    task.url,
                    task.status,
                    task.labels,
                ),
            )

        conn.commit()
    finally:
        conn.close()


def upsert_tasks(tasks: list[RepositoryTask]):
    for task in tasks:
        upsert_task(task)

def get_tasks() -> list[dict]:
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    source,
                    source_id,
                    repository,
                    title,
                    description,
                    url,
                    status,
                    labels,
                    created_at,
                    updated_at
                FROM tasks
                ORDER BY id;
                """
            )

            rows = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": row[0],
            "source": row[1],
            "source_id": row[2],
            "repository": row[3],
            "title": row[4],
            "description": row[5],
            "url": row[6],
            "status": row[7],
            "labels": row[8],
            "created_at": row[9],
            "updated_at": row[10],
        }
        for row in rows
    ]