from app.connectors.gitlab import GitLabConnector


def test_gitlab_auth_headers_without_token():
    connector = GitLabConnector("example/repo")

    headers = connector.get_auth_headers()

    assert "PRIVATE-TOKEN" not in headers
    assert headers["Accept"] == "application/json"


def test_gitlab_auth_headers_with_token():
    connector = GitLabConnector("example/repo", token="test-token")

    headers = connector.get_auth_headers()

    assert headers["PRIVATE-TOKEN"] == "test-token"


def test_gitlab_task_normalization():
    connector = GitLabConnector("example/repo")

    raw_task = {
        "id": 12345,
        "title": "Improve accessibility",
        "description": "Fix keyboard navigation",
        "web_url": "https://gitlab.com/example/repo/-/issues/10",
        "state": "opened",
        "labels": ["accessibility", "frontend"],
    }

    task = connector.normalize_task(raw_task)

    assert task.source == "gitlab"
    assert task.source_id == "12345"
    assert task.title == "Improve accessibility"
    assert task.description == "Fix keyboard navigation"
    assert task.status == "opened"
    assert task.labels == ["accessibility", "frontend"]


def test_fetch_tasks_handles_pagination_and_tracks_rate_limit(monkeypatch):
    first_page = [
        {
            "id": 1,
            "title": "First GitLab issue",
            "description": "First issue description",
            "web_url": "https://gitlab.com/example/repo/-/issues/1",
            "state": "opened",
            "labels": ["civic"],
        }
    ]

    second_page = [
        {
            "id": 2,
            "title": "Second GitLab issue",
            "description": "Second issue description",
            "web_url": "https://gitlab.com/example/repo/-/issues/2",
            "state": "opened",
            "labels": ["backend"],
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
                "ratelimit-limit": "2000",
                "ratelimit-remaining": "1999",
                "ratelimit-reset": "123456",
            },
            {
                "next": {
                    "url": "https://gitlab.com/api/v4/projects/example%2Frepo/issues?page=2"
                }
            },
        ),
        FakeResponse(
            second_page,
            {
                "ratelimit-limit": "2000",
                "ratelimit-remaining": "1998",
                "ratelimit-reset": "123456",
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

    monkeypatch.setattr("app.connectors.gitlab.httpx.Client", FakeClient)

    connector = GitLabConnector("example/repo")
    tasks = connector.fetch_tasks()

    assert len(tasks) == 2
    assert tasks[0].title == "First GitLab issue"
    assert tasks[1].title == "Second GitLab issue"

    assert connector.get_rate_limit_status() == {
        "limit": "2000",
        "remaining": "1998",
        "reset": "123456",
    }
