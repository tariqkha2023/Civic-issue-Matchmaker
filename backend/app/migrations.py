"""Versioned additive migrations retaining original source and participation data."""

import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.store import (
    ActiveClaim,
    Base,
    Contribution,
    JobLease,
    ParticipationEvent,
    SchemaVersion,
)


def migrate(engine):
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        if not db.get(SchemaVersion, 1):
            db.add(SchemaVersion(version=1))
        if not db.get(SchemaVersion, 2):
            keys = set(
                db.execute(
                    select(ParticipationEvent.user_id, ParticipationEvent.task_id)
                ).all()
            )
            keys |= {(c.user_id, c.task_id) for c in db.scalars(select(ActiveClaim))}
            for uid, tid in keys:
                original = list(
                    db.scalars(
                        select(ParticipationEvent)
                        .where(
                            ParticipationEvent.user_id == uid,
                            ParticipationEvent.task_id == tid,
                        )
                        .order_by(ParticipationEvent.id)
                    )
                )
                claim = db.get(ActiveClaim, tid)
                last = original[-1].action if original else "claimed"
                state = (
                    "in_progress"
                    if claim and claim.user_id == uid
                    else "completed"
                    if last == "completed"
                    else "withdrawn"
                )
                db.add(
                    Contribution(
                        user_id=uid,
                        task_id=tid,
                        state=state,
                        note="Migrated local activity; not a GitHub assignment or verified acceptance.",
                        events=[
                            {
                                "state": e.action,
                                "time": e.occurred_at,
                                "basis": "legacy local event",
                            }
                            for e in original
                        ],
                        updated_at=original[-1].occurred_at
                        if original
                        else time.time(),
                    )
                )
            db.add(SchemaVersion(version=2))
        for name in ["scheduler", "role-administration"]:
            if not db.get(JobLease, name):
                db.add(JobLease(name=name))
        db.commit()
