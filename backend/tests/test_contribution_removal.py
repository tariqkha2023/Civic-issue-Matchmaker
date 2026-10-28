"""Own contribution removal, concurrency protection and source independence."""

import pytest
from fastapi.testclient import TestClient
from test_mvp import register, seed

from app.main import app


@pytest.mark.parametrize("state", ["interested", "withdrawn", "completed"])
def test_remove_own_contribution_in_any_state_without_affecting_other_records(
    client, db_engine, state
):
    task_id = seed(db_engine)[0]
    register(client)
    item = client.post(f"/api/tasks/{task_id}/contributions").json()
    activity_id = item["id"]
    client.put(f"/api/me/saved/{task_id}")
    if state == "completed":
        client.put(
            f"/api/me/contributions/{activity_id}", json={"state": "in_progress"}
        )
        assert (
            client.put(
                f"/api/me/contributions/{activity_id}",
                json={"state": "completed", "note": "Finished local work"},
            ).status_code
            == 200
        )
    elif state == "withdrawn":
        client.put(f"/api/me/contributions/{activity_id}", json={"state": state})
    with TestClient(app) as other:
        register(other, "other-removal@example.com")
        other_item = other.post(f"/api/tasks/{task_id}/contributions").json()
        assert other.delete(f"/api/me/contributions/{activity_id}").status_code == 404
        item = client.get("/api/me/contributions").json()[0]
        assert (
            client.delete(
                f"/api/me/contributions/{activity_id}",
                params={"expected_version": item["updated_at"]},
            ).status_code
            == 204
        )
        assert client.get("/api/me/contributions").json() == []
        assert client.get("/api/me/export").json()["contributions"] == []
        assert [r["id"] for r in other.get("/api/me/contributions").json()] == [
            other_item["id"]
        ]
    task = client.get(f"/api/tasks/{task_id}").json()
    assert task["status"] == "open" and not task["tracking"] and task["saved"]
    assert (
        client.post(f"/api/tasks/{task_id}/contributions").json()["state"]
        == "interested"
    )


def test_removal_rejects_stale_view_and_requires_signin(client, db_engine):
    task_id = seed(db_engine)[0]
    register(client)
    item = client.post(f"/api/tasks/{task_id}/contributions").json()
    url = f"/api/me/contributions/{item['id']}"
    assert (
        client.delete(
            url, params={"expected_version": item["updated_at"] - 1}
        ).status_code
        == 409
    )
    assert len(client.get("/api/me/contributions").json()) == 1
    client.delete("/api/sessions")
    assert client.delete(url).status_code == 401
