import os
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.main import app
from app.store import Base, get_db, make_engine


@pytest.fixture
def db_engine():
    test_url = os.getenv("TEST_DATABASE_URL")
    if test_url:
        # An isolated schema prevents tests from touching application tables.
        root_engine = make_engine(test_url)
        schema = "test_civic_" + uuid4().hex
        with root_engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        engine = root_engine.execution_options(schema_translate_map={None: schema})
    else:
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    Base.metadata.create_all(engine)
    yield engine
    if test_url:
        with root_engine.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
    engine.dispose()


@pytest.fixture
def client(db_engine, monkeypatch):
    @asynccontextmanager
    async def isolated_lifespan(app):
        yield

    # Fixtures already created the schema. Never initialize a developer database.
    monkeypatch.setattr(app.router, "lifespan_context", isolated_lifespan)

    def test_db():
        with Session(db_engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def legacy_storage_database(request, monkeypatch):
    """Keep the older PostgreSQL storage tests away from application tables."""
    if request.module.__name__ not in {"test_task_storage", "test_task_aggregation"}:
        yield
        return
    test_url = os.getenv("TEST_DATABASE_URL")
    if not test_url:
        pytest.skip("Legacy storage integration requires TEST_DATABASE_URL (PostgreSQL).")
    import psycopg
    from psycopg import sql

    from app import task_storage

    schema = "legacy_test_" + uuid4().hex
    with psycopg.connect(test_url, autocommit=True) as root:
        root.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    def connection():
        return psycopg.connect(test_url, options=f"-c search_path={schema}")
    monkeypatch.setattr(task_storage, "get_connection", connection)
    monkeypatch.setattr(request.module, "get_connection", connection)
    try:
        yield
    finally:
        with psycopg.connect(test_url, autocommit=True) as root:
            root.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
