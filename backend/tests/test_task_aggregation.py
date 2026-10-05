from app.connectors.base import RepositoryConnector
from app.connectors.models import RepositoryTask
from app.database import get_connection
from app.task_aggregation import aggregate_tasks
from app.task_storage import create_tasks_table


class FakeConnector(RepositoryConnector):
    def fetch_tasks(self) -> list[RepositoryTask]:
        return [
            RepositoryTask(
                source="github",
                source_id="3001",
                repository="example/project",
                title="Aggregation test task",
                description="Stored through aggregation service",
                url="https://example.com/issues/3001",
                status="open",
                labels=["aggregation"],
            )
        ]

    def get_auth_headers(self) -> dict[str, str]:
        return {}

    def get_rate_limit_status(self) -> dict:
        return {}

    def get_next_page(self, response) -> str | None:
        return None

    def normalize_task(self, raw_task: dict) -> RepositoryTask:
        raise NotImplementedError


def test_aggregate_tasks_fetches_and_stores_tasks():
    create_tasks_table()

    connector = FakeConnector()

    count = aggregate_tasks(connector)

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT title, repository
                FROM tasks
                WHERE source = %s AND source_id = %s;
                """,
                ("github", "3001"),
            )

            row = cursor.fetchone()
    finally:
        conn.close()

    assert count == 1
    assert row == (
        "Aggregation test task",
        "example/project",
    )