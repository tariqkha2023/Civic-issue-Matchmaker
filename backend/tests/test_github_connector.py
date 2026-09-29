from app.connectors.github import GitHubConnector


def test_github_auth_headers_without_token():
    connector = GitHubConnector("example", "repo")

    headers = connector.get_auth_headers()

    assert "Authorization" not in headers
    assert headers["Accept"] == "application/vnd.github+json"


def test_github_auth_headers_with_token():
    connector = GitHubConnector(
        "example",
        "repo",
        token="test-token",
    )

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
    