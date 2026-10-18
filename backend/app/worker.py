"""Scheduled, resumable source scans and daily SQLite backups."""

import argparse
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.github_sync import acquire, release, sync_source
from app.projects import settings
from app.store import Repository, engine

log = logging.getLogger(__name__)


def backup_sqlite(db_engine=engine, directory=None):
    if (
        db_engine.dialect.name != "sqlite"
        or not db_engine.url.database
        or db_engine.url.database == ":memory:"
    ):
        return None
    folder = Path(directory or os.getenv("BACKUP_DIR", "./backups"))
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (time.strftime("civic-%Y-%m-%d") + ".db")
    if not target.exists():
        temp = target.with_suffix(".tmp")
        with (
            sqlite3.connect(db_engine.url.database) as src,
            sqlite3.connect(temp) as dst,
        ):
            src.backup(dst)
        os.chmod(temp, 0o600)
        temp.replace(target)
    backups = sorted(folder.glob("civic-*.db"))
    for old in backups[:-7]:
        old.unlink()
    return target


def tick(db_engine=engine):
    with Session(db_engine) as db:
        if not acquire(db, "scheduler"):
            return
        try:
            for repo in db.scalars(
                select(Repository).where(
                    Repository.source == "github", Repository.enabled.is_(True)
                )
            ).all():
                config = settings(db, repo)
                if config.get("next_due", 0) <= time.time():
                    sync_source(db, repo)
            backup_sqlite(db_engine)
        finally:
            release(db, "scheduler")


def loop(stop, db_engine=engine):
    while not stop.is_set():
        try:
            tick(db_engine)
        except Exception:
            # Avoid logging HTTP request objects/tokens. Admin status is persisted by scans.
            log.error("Scheduled worker operation failed; will retry.")
        stop.wait(15)


def start(db_engine=engine):
    stop = threading.Event()
    thread = threading.Thread(
        target=loop, args=(stop, db_engine), daemon=True, name="civic-source-worker"
    )
    thread.start()
    return stop, thread


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    from app.migrations import migrate

    migrate(engine)
    if args.once:
        tick()
    else:
        loop(threading.Event())
