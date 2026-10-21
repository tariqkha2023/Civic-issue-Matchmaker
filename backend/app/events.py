"""Idempotent in-app delivery with user preferences and recorded outcomes."""

from sqlalchemy.exc import IntegrityError

from app.store import AccountSettings, EventDelivery, Notification


def preferences(db, user_id):
    row = db.get(AccountSettings, user_id)
    return {
        "new_matches": True,
        "activity": True,
        "minimum_score": 60,
        **(row.preferences if row else {}),
    }


def deliver(db, user_id, key, title, body="", category="activity"):
    identity = f"{user_id}:{key}"
    if db.get(EventDelivery, identity):
        return
    enabled = preferences(db, user_id).get(category, True)
    try:
        with db.begin_nested():
            db.add(
                EventDelivery(
                    key=identity,
                    user_id=user_id,
                    status="delivered" if enabled else "suppressed",
                )
            )
            if enabled:
                db.add(
                    Notification(user_id=user_id, title=title[:200], body=body[:1000])
                )
            db.flush()
    except IntegrityError:
        pass  # A concurrent scan already delivered this event.
