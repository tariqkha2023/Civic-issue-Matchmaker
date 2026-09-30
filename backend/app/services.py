"""Domain services for authorization, participation and metadata management."""


from fastapi import HTTPException


from sqlalchemy import delete, select


from sqlalchemy.exc import IntegrityError


from app.store import (
    AccountRole,
    ActiveClaim,
    AuditEntry,
    MaintainerAccess,
    MetadataCorrection,
    ParticipationEvent,
    Repository,
    Task,
    User,
)


def roles(db, user):
    return [
        "volunteer",
        *sorted(
            db.scalars(select(AccountRole.role).where(AccountRole.user_id == user.id))
        ),
    ]


def require_admin(db, user):
    if "administrator" not in roles(db, user):
        raise HTTPException(403, "Administrator access required.")


def can_maintain(db, user, repository_id):
    assigned = (
        "maintainer" in roles(db, user)
        and db.get(MaintainerAccess, (user.id, repository_id)) is not None
    )
    return "administrator" in roles(db, user) or assigned


def assign_roles(db, actor, user_id, granted, repository_ids):
    require_admin(db, actor)
    # Serialize role changes so concurrent requests cannot remove the last admin.
    db.scalars(select(User).order_by(User.id).with_for_update()).all()
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "Account not found.")
    if "administrator" in roles(db, target) and "administrator" not in granted:
        admins = db.scalars(
            select(AccountRole).where(AccountRole.role == "administrator")
        ).all()
        if len(admins) <= 1:
            raise HTTPException(409, "Keep at least one administrator account.")
    if repository_ids and "maintainer" not in granted:
        raise HTTPException(422, "Repository assignments require the maintainer role.")
    if any(db.get(Repository, rid) is None for rid in repository_ids):
        raise HTTPException(422, "Unknown repository assignment.")
    before = roles(db, target)
    db.execute(delete(AccountRole).where(AccountRole.user_id == user_id))
    db.execute(delete(MaintainerAccess).where(MaintainerAccess.user_id == user_id))
    db.add_all([AccountRole(user_id=user_id, role=r) for r in set(granted)])
    db.add_all(
        [
            MaintainerAccess(user_id=user_id, repository_id=r)
            for r in set(repository_ids)
        ]
    )
    db.add(
        AuditEntry(
            actor_id=actor.id,
            action="roles.assigned",
            target=f"user:{user_id}",
            details={
                "before": before,
                "roles": granted,
                "repositories": repository_ids,
            },
        )
    )
    db.commit()
    return target

