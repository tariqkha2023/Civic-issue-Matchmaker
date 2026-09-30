"""Additive versioned schema initialization; existing accounts/tasks are untouched."""

from sqlalchemy.orm import Session

from app.store import Base, SchemaVersion


def migrate(engine):
    # Version 1 only introduces tables, so create_all is idempotent for legacy DBs.
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        if not db.get(SchemaVersion, 1):
            db.add(SchemaVersion(version=1))
            db.commit()
