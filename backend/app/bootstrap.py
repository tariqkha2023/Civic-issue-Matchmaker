"""Explicit local demo-account setup; never runs during public signup."""

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.migrations import migrate
from app.projects import configure_sources
from app.security import hash_password
from app.store import AccountRole, MaintainerAccess, Repository, User, engine


def seed_accounts(db):
    configure_sources(db)
    repositories = list(
        db.scalars(select(Repository).where(Repository.source == "github"))
    )
    credentials = []
    for role, name in [
        ("volunteer", "Demo Contributor"),
        ("maintainer", "Demo Curator"),
        ("administrator", "Demo Administrator"),
    ]:
        email = f"{role}@civic.demo"
        user = db.scalar(select(User).where(User.email == email))
        if user:
            if role == "maintainer" and db.get(AccountRole, (user.id, role)):
                for repo in repositories:
                    if not db.get(MaintainerAccess, (user.id, repo.id)):
                        db.add(MaintainerAccess(user_id=user.id, repository_id=repo.id))
            continue  # Keep existing passwords, profiles and role assignments.
        password = "Civic-" + secrets.token_urlsafe(12)
        user = User(
            email=email,
            password_hash=hash_password(password),
            profile={
                "name": name,
                "skills": ["python", "javascript", "documentation"],
                "interests": ["humanitarian mapping", "open mapping"],
                "hours": 4,
                "level": "Beginner",
                "difficulty": "Beginner",
                "repositories": [],
            },
        )
        db.add(user)
        db.flush()
        if role != "volunteer":
            db.add(AccountRole(user_id=user.id, role=role))
        if role == "maintainer":
            for repo in repositories:
                db.add(MaintainerAccess(user_id=user.id, repository_id=repo.id))
        credentials.append((email, password))
    db.commit()
    return credentials


if __name__ == "__main__":
    migrate(engine)
    with Session(engine) as db:
        for email, password in seed_accounts(db):
            print(f"{email}: {password}")
