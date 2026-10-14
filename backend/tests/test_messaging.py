from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_mvp import register, seed

from app.main import app
from app.store import AccountRole, User


def second_client(email):
    c = TestClient(app)
    register(c, email)
    return c


def uid(db_engine, email):
    with Session(db_engine) as db:
        return db.scalar(select(User.id).where(User.email == email))


def make_staff(db_engine, email):
    with Session(db_engine) as db:
        db.add(AccountRole(user_id=uid(db_engine, email), role="maintainer"))
        db.commit()


def test_welcome_and_task_notifications(client, db_engine):
    register(client)
    seed(db_engine)
    items = client.get("/api/me/notifications").json()
    assert items[0]["title"].startswith("Welcome") and items[0]["read"] is False
    assert client.get("/api/me/unread").json() == {"notifications": 1, "messages": 0}
    assert client.put("/api/me/saved/1").status_code == 204
    assert client.get("/api/me/unread").json()["notifications"] == 2
    client.post("/api/tasks/1/participation", json={"action": "claimed"})
    titles = [n["title"] for n in client.get("/api/me/notifications").json()]
    assert "Task claimed" in titles and "Task saved" in titles
    first = client.get("/api/me/notifications").json()[0]["id"]
    assert client.put(f"/api/me/notifications/{first}/read").status_code == 204
    assert client.post("/api/me/notifications/read").status_code == 204
    assert client.get("/api/me/unread").json()["notifications"] == 0


def test_notifications_are_private(client, db_engine):
    register(client)
    mine = client.get("/api/me/notifications").json()[0]["id"]
    other = second_client("other@example.com")
    assert other.put(f"/api/me/notifications/{mine}/read").status_code == 404
    assert all(n["id"] != mine for n in other.get("/api/me/notifications").json())


def test_notifications_require_login(client):
    assert client.get("/api/me/notifications").status_code == 401
    assert client.get("/api/me/unread").status_code == 401
    assert client.post("/api/messages", json={"recipient_id": 1, "body": "x"}).status_code == 401


def test_message_flow_with_staff(client, db_engine):
    register(client, "staff@example.com")
    make_staff(db_engine, "staff@example.com")
    vol = second_client("vol@example.com")
    staff_id, vol_id = uid(db_engine, "staff@example.com"), uid(db_engine, "vol@example.com")
    # Volunteers see staff as contacts.
    assert [c["user_id"] for c in vol.get("/api/messages/conversations").json()] == [staff_id]
    assert vol.post("/api/messages", json={"recipient_id": staff_id, "body": "  Hello  "}).status_code == 201
    assert client.get("/api/me/unread").json()["messages"] == 1
    convo = client.get("/api/messages/conversations").json()
    assert convo[0]["user_id"] == vol_id and convo[0]["unread"] == 1
    thread = client.get(f"/api/messages/{vol_id}").json()
    assert thread["messages"][0]["body"] == "Hello" and thread["messages"][0]["mine"] is False
    assert client.get("/api/me/unread").json()["messages"] == 0  # opening marks read
    # Staff can reply, and then the volunteer can answer back.
    assert client.post("/api/messages", json={"recipient_id": vol_id, "body": "Hi!"}).status_code == 201
    assert vol.get("/api/me/unread").json()["messages"] == 1


def test_volunteers_cannot_cold_message_each_other(client, db_engine):
    register(client, "a@example.com")
    second_client("b@example.com")
    r = client.post("/api/messages", json={"recipient_id": uid(db_engine, "b@example.com"), "body": "hi"})
    assert r.status_code == 403


def test_message_validation(client, db_engine):
    register(client, "staff2@example.com")
    make_staff(db_engine, "staff2@example.com")
    vol = second_client("v2@example.com")
    sid = uid(db_engine, "staff2@example.com")
    assert vol.post("/api/messages", json={"recipient_id": sid, "body": "   "}).status_code == 422
    assert vol.post("/api/messages", json={"recipient_id": sid, "body": "x" * 2001}).status_code == 422
    assert vol.post("/api/messages", json={"recipient_id": 9999, "body": "hi"}).status_code == 404
    assert vol.get("/api/messages/9999").status_code == 404
