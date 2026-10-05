import pytest

from app.connectors.base import RepositoryConnector
from app.connectors.models import RepositoryTask


class IncompleteConnector(RepositoryConnector):
    pass


class ExampleConnector(RepositoryConnector):
    def fetch_tasks(self) -> list[RepositoryTask]:
        return []

    def get_auth_headers(self) -> dict[str, str]:
        return {}

    def get_rate_limit_status(self) -> dict:
        return {"remaining": 100}

    def get_next_page(self, response) -> str | None:
        return None

    def normalize_task(self, raw_task: dict) -> RepositoryTask:
        return RepositoryTask(
            source="example",
            source_id=str(raw_task["id"]),
            repository="example/repository",
            title=raw_task["title"],
            description=raw_task.get("description", ""),
            url=raw_task["url"],
            status=raw_task["status"],
            labels=raw_task.get("labels", []),
        )

def test_incomplete_connector_cannot_be_created():
    with pytest.raises(TypeError):
        IncompleteConnector()


def test_connector_can_normalize_task():
    connector = ExampleConnector()

    raw_task = {
        "id": 123,
        "title": "Fix accessibility issue",
        "description": "Improve keyboard navigation",
        "url": "https://example.com/issues/123",
        "status": "open",
        "labels": ["accessibility", "frontend"],
    }

    task = connector.normalize_task(raw_task)

    assert task.source == "example"
    assert task.source_id == "123"
    assert task.title == "Fix accessibility issue"
    assert task.status == "open"
    assert task.labels == ["accessibility", "frontend"]