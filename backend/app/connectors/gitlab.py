from urllib.parse import quote

import httpx

from app.connectors.base import RepositoryConnector
from app.connectors.models import RepositoryTask


class GitLabConnector(RepositoryConnector):
    BASE_URL = "https://gitlab.com/api/v4"

    def __init__(self, project: str, token: str | None = None):
        self.project = project
        self.token = token
        self._rate_limit = {}

    def get_auth_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
        }

        if self.token:
            headers["PRIVATE-TOKEN"] = self.token

        return headers

    def normalize_task(self, raw_task: dict) -> RepositoryTask:
        return RepositoryTask(
            source="gitlab",
            source_id=str(raw_task["id"]),
            title=raw_task["title"],
            description=raw_task.get("description") or "",
            url=raw_task["web_url"],
            status=raw_task["state"],
            labels=raw_task.get("labels", []),
        )

    def get_next_page(self, response: httpx.Response) -> str | None:
        next_link = response.links.get("next")

        if next_link:
            return next_link["url"]

        return None

    def get_rate_limit_status(self) -> dict:
        return self._rate_limit

    def fetch_tasks(self) -> list[RepositoryTask]:
        encoded_project = quote(self.project, safe="")
        url = f"{self.BASE_URL}/projects/{encoded_project}/issues"

        params = {
            "state": "opened",
            "per_page": 100,
        }

        tasks = []

        with httpx.Client(
            headers=self.get_auth_headers(),
            timeout=10.0,
        ) as client:
            while url:
                response = client.get(url, params=params)
                response.raise_for_status()

                self._rate_limit = {
                    "limit": response.headers.get("ratelimit-limit"),
                    "remaining": response.headers.get("ratelimit-remaining"),
                    "reset": response.headers.get("ratelimit-reset"),
                }

                for raw_task in response.json():
                    tasks.append(self.normalize_task(raw_task))

                url = self.get_next_page(response)
                params = None

        return tasks
