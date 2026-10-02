"""Operator-only repository configuration and scan command."""

import argparse
import os
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion import scan_repository
from app.store import Base, Repository, engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add-source")
    add.add_argument("source", choices=["github", "gitlab"])
    add.add_argument("path", help="owner/repository or GitLab namespace/project")
    add.add_argument(
        "--label",
        action="append",
        default=[],
        help="Optional eligible label; repeat to select any of several labels",
    )
    disable = sub.add_parser("disable-source")
    disable.add_argument("id", type=int)
    sub.add_parser("scan")
    sub.add_parser("list-sources")
    args = parser.parse_args()
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        if args.command == "add-source":
            pattern = (
                r"[\w.-]+/[\w.-]+"
                if args.source == "github"
                else r"[\w.-]+(?:/[\w.-]+)+"
            )
            if not re.fullmatch(pattern, args.path) or any(
                part in {".", ".."} for part in args.path.split("/")
            ):
                parser.error("Use a valid namespace/project path.")
            repo = db.scalar(
                select(Repository).where(
                    Repository.source == args.source, Repository.path == args.path
                )
            )
            if not repo:
                repo = Repository(source=args.source, path=args.path)
                db.add(repo)
            repo.enabled = True
            repo.selection_labels = args.label
            db.commit()
            print(f"Configured source {repo.id}: {repo.source}/{repo.path}")
        elif args.command == "disable-source":
            repo = db.get(Repository, args.id)
            if not repo:
                parser.error("Unknown source ID")
            repo.enabled = False
            db.commit()
        elif args.command == "list-sources":
            for repo in db.scalars(select(Repository).order_by(Repository.id)):
                print(
                    repo.id,
                    repo.source,
                    repo.path,
                    "enabled" if repo.enabled else "disabled",
                    repo.scan_error or "ok",
                )
        else:
            failed = False
            for repo in db.scalars(
                select(Repository).where(
                    Repository.enabled.is_(True),
                    Repository.source.in_(["github", "gitlab"]),
                )
            ).all():
                try:
                    count = scan_repository(
                        db, repo, os.getenv(f"{repo.source.upper()}_TOKEN")
                    )
                    print(f"{repo.path}: imported {count} open tasks")
                except RuntimeError as exc:
                    failed = True
                    print(f"{repo.path}: {exc}")
            if failed:
                raise SystemExit(1)


if __name__ == "__main__":
    main()
