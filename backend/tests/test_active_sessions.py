"""Exercise 500 active identities without touching a developer database."""

import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.main import app
from app.security import token_hash
from app.store import Base, LoginSession, User, get_db, make_engine


def test_500_active_sessions_preserve_identity_under_parallel_reads(client, tmp_path):
    engine = make_engine("sqlite:///" + str(tmp_path / "sessions.db"))
    Base.metadata.create_all(engine)
    tokens = [f"isolated-test-session-{index}" for index in range(500)]
    with Session(engine) as db:
        for index, token in enumerate(tokens):
            user = User(
                email=f"user-{index}@example.test",
                password_hash="unused-test-hash",
                profile={"name": f"User {index}"},
            )
            db.add(user)
            db.flush()
            db.add(
                LoginSession(
                    token_hash=token_hash(token),
                    user_id=user.id,
                    last_activity=time.time(),
                )
            )
        db.commit()

    def isolated_db():
        with Session(engine) as db:
            yield db

    previous = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = isolated_db
    try:

        def probe(index):
            response = client.get(
                "/api/me", headers={"Cookie": "civic_session=" + tokens[index]}
            )
            assert response.status_code == 200
            assert response.json()["profile"]["name"] == f"User {index}"

        with ThreadPoolExecutor(max_workers=32) as workers:
            list(workers.map(probe, range(500)))
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(LoginSession)) == 500
    finally:
        app.dependency_overrides[get_db] = previous
        engine.dispose()
