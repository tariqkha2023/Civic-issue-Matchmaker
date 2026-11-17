"""Task response projection using effective, source-preserving metadata."""

from sqlalchemy import select

from app.discovery_context import reviewed_context
from app.enrichment import effective_metadata, project_context
from app.matching import SCORE_VERSION, evidence_strength, score
from app.store import (
    AccountRole,
    Contribution,
    IssueEnrichment,
    IssueInfo,
    IssueResearch,
    MaintainerAccess,
    MetadataCorrection,
    RelevanceFeedback,
    SourceSettings,
)
from app.task_guidance import task_guidance


def projection_context(db, user, task_ids=None):
    def rows(model):
        if task_ids is None:
            return list(db.scalars(select(model)))
        ids = list(task_ids)
        result = []
        for start in range(0, len(ids), 1000):
            result.extend(
                db.scalars(
                    select(model).where(model.task_id.in_(ids[start : start + 1000]))
                )
            )
        return result

    return {
        "enrichments": {r.task_id: r for r in rows(IssueEnrichment)},
        "research": {r.task_id: r for r in rows(IssueResearch)},
        "info": {r.task_id: r.fields for r in rows(IssueInfo)},
        "corrections": {r.task_id: r.fields for r in rows(MetadataCorrection)},
        "projects": {
            r.repository_id: r.fields for r in db.scalars(select(SourceSettings))
        },
        "roles": set(
            db.scalars(select(AccountRole.role).where(AccountRole.user_id == user.id))
        ),
        "scopes": set(
            db.scalars(
                select(MaintainerAccess.repository_id).where(
                    MaintainerAccess.user_id == user.id
                )
            )
        ),
        "feedback": {
            r.task_id: r
            for r in db.scalars(
                select(RelevanceFeedback).where(RelevanceFeedback.user_id == user.id)
            )
        },
        "tracking": set(
            db.scalars(
                select(Contribution.task_id).where(
                    Contribution.user_id == user.id,
                    Contribution.state.in_(["interested", "in_progress", "submitted"]),
                )
            )
        ),
        "completed": set(
            db.scalars(
                select(Contribution.task_id).where(
                    Contribution.user_id == user.id, Contribution.state == "completed"
                )
            )
        ),
    }


def task_view(task, repo, saved=False, profile=None, db=None, user=None, context=None):
    if context is None and db is not None and user is not None:
        context = projection_context(db, user, [task.id])
    context = context or {
        "corrections": {},
        "info": {},
        "projects": {},
        "roles": set(),
        "scopes": set(),
        "feedback": {},
        "tracking": set(),
        "completed": set(),
    }
    correction = context["corrections"].get(task.id, {})
    metadata = effective_metadata(
        task,
        context.get("enrichments", {}).get(task.id),
        correction,
        project_context(context["projects"][repo.id])
        if repo.id in context["projects"]
        else {},
        context.get("research", {}).get(task.id),
    )
    feedback = context["feedback"].get(task.id)
    review = reviewed_context(
        task, context.get("research", {}).get(task.id),
        project_context(context["projects"][repo.id]) if repo.id in context["projects"] else {},
    )
    uncertainties = (
        [review.get("uncertainty", "")]
        if review
        else (metadata.get("interpretation") or {}).get("uncertainties", [])
    )
    guidance = task_guidance(uncertainties)
    if review and review.get("review_notes"):
        guidance["review_notes"] = task_guidance([review["review_notes"]])["review_notes"]
    data = {
        "id": task.id,
        "score_version": SCORE_VERSION,
        "title": task.title,
        "description": task.description,
        "url": task.url,
        "status": task.status,
        "repository": repo.path,
        "source": repo.source,
        "labels": task.labels,
        "metadata": metadata,
        "source_skills": task.metadata_fields.get("skills", []),
        "first_seen": task.first_seen,
        "last_successful_scan": repo.last_success,
        "source_error": repo.scan_error,
        "saved": saved,
        "upstream": context["info"].get(task.id, {}),
        "project": context["projects"].get(repo.id, {}),
        "reviewed_context": review,
        "clarifications": guidance,
        "source_enabled": repo.enabled,
        "metadata_origin": "curator reviewed"
        if correction
        else "AI enriched + source labels"
        if metadata.get("ai_model")
        else "saved research + source labels"
        if metadata.get("research_evidence")
        else "source derived",
        "can_manage": "administrator" in context["roles"]
        or ("maintainer" in context["roles"] and repo.id in context["scopes"]),
        "tracking": task.id in context["tracking"],
        "feedback": {"relevant": feedback.relevant, "explanation": feedback.explanation}
        if feedback
        else None,
        "coverage": evidence_strength(metadata),
    }
    if profile is not None:
        data["score"], data["explanations"] = score(
            profile,
            metadata,
            repo.path,
            {
                "relevance": feedback.relevant if feedback else None,
                "completed": task.id in context["completed"],
            },
        )
    if db is not None and user is not None and repo.source != "github":
        from app.services import participation

        data["participation"] = participation(db, user, task)
    return data
