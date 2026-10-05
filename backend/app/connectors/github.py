import httpx

from app.connectors.base import RepositoryConnector
from app.connectors.models import RepositoryTask


class GitHubConnector(RepositoryConnector):
    BASE_URL = "https://api.github.com"

    def __init__(self, owner: str, repo: str, token: str | None = None):
        self.owner = owner
        self.repo = repo
        self.token = token
        self._rate_limit = {}

    def get_auth_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    def normalize_task(self, raw_task: dict) -> RepositoryTask:
        labels = [label["name"] for label in raw_task.get("labels", [])]

        return RepositoryTask(
            source="github",
            source_id=str(raw_task["id"]),
            repository=f"{self.owner}/{self.repo}",
            title=raw_task["title"],
            description=raw_task.get("body") or "",
            url=raw_task["html_url"],
            status=raw_task["state"],
            labels=labels,
            )

    def get_next_page(self, response: httpx.Response) -> str | None:
        next_link = response.links.get("next")

        if next_link:
            return next_link["url"]

        return None

    def get_rate_limit_status(self) -> dict:
        return self._rate_limit

    def fetch_tasks(self) -> list[RepositoryTask]:
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/issues"

        params = {
            "state": "open",
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
                    "limit": response.headers.get("x-ratelimit-limit"),
                    "remaining": response.headers.get("x-ratelimit-remaining"),
                    "reset": response.headers.get("x-ratelimit-reset"),
                }

                for raw_task in response.json():
                    # GitHub's issues endpoint also returns pull requests.
                    if "pull_request" in raw_task:
                        continue

                    tasks.append(self.normalize_task(raw_task))

                url = self.get_next_page(response)

                # The next-page URL already contains query parameters.
                params = None

        return tasks

    