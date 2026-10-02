"""Explicit local demo-account setup; never runs during public signup."""

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.demo import get_demo_repository, seed_demo
from app.migrations import migrate
from app.security import hash_password
from app.store import AccountRole, MaintainerAccess, User, engine


def seed_accounts(db):
    seed_demo(db)
    repo = get_demo_repository(db)
    credentials = []
    for role, name in [
        ("volunteer", "Demo Volunteer"),
        ("maintainer", "Demo Maintainer"),
        ("administrator", "Demo Administrator"),
    ]:
        email = f"{role}@civic.demo"
        user = db.scalar(select(User).where(User.email == email))
        if user:
            continue  # Keep existing passwords, profiles and role assignments.
        password = "Civic-" + secrets.token_urlsafe(12)
        user = User(
            email=email,
            password_hash=hash_password(password),
            profile={
                "name": name,
                "skills": ["communication", "teamwork"],
                "interests": ["food security"],
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
            db.add(MaintainerAccess(user_id=user.id, repository_id=repo.id))
        credentials.append((email, password))
    db.commit()
    return credentials


if __name__ == "__main__":
    migrate(engine)
    with Session(engine) as db:
        for email, password in seed_accounts(db):
            print(f"{email}: {password}")
