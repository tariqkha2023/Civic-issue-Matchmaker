from abc import ABC, abstractmethod

from app.connectors.models import RepositoryTask


class RepositoryConnector(ABC):
    @abstractmethod
    def fetch_tasks(self) -> list[RepositoryTask]:
        """Retrieve and normalize tasks from the external source."""

    @abstractmethod
    def get_auth_headers(self) -> dict[str, str]:
        """Return authentication headers required by the source API."""

    @abstractmethod
    def get_rate_limit_status(self) -> dict:
        """Return current API rate-limit information."""

    @abstractmethod
    def get_next_page(self, response) -> str | None:
        """Return the URL or identifier for the next page, if one exists."""

    @abstractmethod
    def normalize_task(self, raw_task: dict) -> RepositoryTask:
        """Convert a source-specific task into the common task format."""
