from app.connectors.github import GitHubConnector


def test_github_auth_headers_without_token():
    connector = GitHubConnector("example", "repo")

    headers = connector.get_auth_headers()

    assert "Authorization" not in headers
    assert headers["Accept"] == "application/vnd.github+json"


def test_github_auth_headers_with_token():
    connector = GitHubConnector("example", "repo", token="test-token")

    headers = connector.get_auth_headers()

    assert headers["Authorization"] == "Bearer test-token"


def test_github_task_normalization():
    connector = GitHubConnector("example", "repo")

    raw_task = {
        "id": 12345,
        "title": "Improve accessibility",
        "body": "Fix keyboard navigation",
        "html_url": "https://github.com/example/repo/issues/10",
        "state": "open",
        "labels": [
            {"name": "accessibility"},
            {"name": "frontend"},
        ],
    }

    task = connector.normalize_task(raw_task)

    assert task.source == "github"
    assert task.source_id == "12345"
    assert task.title == "Improve accessibility"
    assert task.description == "Fix keyboard navigation"
    assert task.status == "open"
    assert task.labels == ["accessibility", "frontend"]


def test_fetch_tasks_handles_pagination_filters_prs_and_tracks_rate_limit(
    monkeypatch,
):
    first_page = [
        {
            "id": 1,
            "title": "First civic issue",
            "body": "First issue description",
            "html_url": "https://github.com/example/repo/issues/1",
            "state": "open",
            "labels": [{"name": "civic"}],
        },
        {
            "id": 2,
            "title": "This is a pull request",
            "body": "Should be ignored",
            "html_url": "https://github.com/example/repo/pull/2",
            "state": "open",
            "labels": [],
            "pull_request": {},
        },
    ]

    second_page = [
        {
            "id": 3,
            "title": "Second civic issue",
            "body": "Second issue description",
            "html_url": "https://github.com/example/repo/issues/3",
            "state": "open",
            "labels": [{"name": "backend"}],
        }
    ]

    class FakeResponse:
        def __init__(self, data, headers, links):
            self._data = data
            self.headers = headers
            self.links = links

        def json(self):
            return self._data

        def raise_for_status(self):
            pass

    responses = [
        FakeResponse(
            first_page,
            {
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "4999",
                "x-ratelimit-reset": "123456",
            },
            {
                "next": {
                    "url": "https://api.github.com/repos/example/repo/issues?page=2"
                }
            },
        ),
        FakeResponse(
            second_page,
            {
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "4998",
                "x-ratelimit-reset": "123456",
            },
            {},
        ),
    ]

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.responses = iter(responses)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def get(self, url, params=None):
            return next(self.responses)

    monkeypatch.setattr("app.connectors.github.httpx.Client", FakeClient)

    connector = GitHubConnector("example", "repo")
    tasks = connector.fetch_tasks()

    assert len(tasks) == 2
    assert tasks[0].title == "First civic issue"
    assert tasks[1].title == "Second civic issue"

    assert connector.get_rate_limit_status() == {
        "limit": "5000",
        "remaining": "4998",
        "reset": "123456",
    }
