from app.connectors.base import RepositoryConnector
from app.task_storage import upsert_tasks


def aggregate_tasks(connector: RepositoryConnector) -> int:
    tasks = connector.fetch_tasks()
    upsert_tasks(tasks)

    return len(tasks)