import os
from contextlib import asynccontextmanager
from typing import Annotated, Literal
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import tasks as task_services
from app.accounts import (
    Credentials,
    Profile,
    Registration,
    check_auth_limit,
    current_user,
    establish_session,
    record_auth,
    user_view,
)
from app.application import router
from app.demo import DEMO_PATH
from app.discovery import discover
from app.migrations import migrate
from app.security import hash_password, token_hash, verify_password
from app.store import (
    LoginSession,
    Repository,
    SavedTask,
    Task,
    User,
    engine,
    get_db,
)
from app.views import task_view


@asynccontextmanager
async def lifespan(app):
    migrate(engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def reject_cross_site_writes(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        allowed = os.getenv("APP_ORIGIN", "http://localhost:5173").split(",")
        if request.headers.get("sec-fetch-site") == "cross-site" or (
            origin and origin not in allowed
        ):
            return Response("Cross-site request rejected", status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def root():
    return {"message": "Civic Issue Matchmaker backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check(db: Annotated[Session, Depends(get_db)]):
    db.execute(text("SELECT 1"))
    return {"database": "ok"}


@app.post("/api/accounts", status_code=201)
def register(
    body: Registration,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    check_auth_limit(db, request, body.email)
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        profile=Profile(name=body.name).model_dump(),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        record_auth(db, request, body.email, "register", False)
        raise HTTPException(409, "An account with that email already exists.") from None
    record_auth(db, request, body.email, "register", True, user.id)
    return establish_session(db, user, response)


@app.post("/api/sessions")
def login(
    body: Credentials,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    check_auth_limit(db, request, body.email)
    user = db.scalar(select(User).where(User.email == body.email))
    # Hash even for unknown accounts to reduce identity timing leakage.
    if not user:
        hash_password(body.password)
    if not user or not verify_password(body.password, user.password_hash):
        record_auth(db, request, body.email, "login", False)
        raise HTTPException(401, "Email or password is incorrect.")
    record_auth(db, request, body.email, "login", True, user.id)
    return establish_session(db, user, response)


@app.delete("/api/sessions", status_code=204)
def logout(
    request: Request, response: Response, db: Annotated[Session, Depends(get_db)]
):
    token = request.cookies.get("civic_session")
    session = db.get(LoginSession, token_hash(token)) if token else None
    if session:
        db.delete(session)
        db.commit()
    response.delete_cookie("civic_session", path="/")


@app.get("/api/me")
def me(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return user_view(user, db)


@app.put("/api/me/profile")
def update_profile(
    body: Profile,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    user.profile = body.model_dump()
    db.commit()
    return user_view(user, db)


class ManualTaskInput(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=10000)
    project: str = Field(min_length=2, max_length=100)
    skills: list[str] = Field(default_factory=list, max_length=30)
    topic: str = Field(default="", max_length=100)
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] | None = None
    effort: float | None = Field(default=None, ge=0, le=10000, allow_inf_nan=False)
    url: str = Field(default="", max_length=2000)
    location: str = Field(default="", max_length=200)
    organizer: str = Field(default="", max_length=100)

    @field_validator("title", "project")
    @classmethod
    def trim_required(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Use at least two non-space characters")
        return value.strip()

    @field_validator("skills")
    @classmethod
    def clean_skills(cls, values):
        return Profile.clean_lists(values)

    @field_validator("topic", "url", "location", "organizer")
    @classmethod
    def trim_optional(cls, value):
        return value.strip()

    @field_validator("url")
    @classmethod
    def safe_url(cls, value):
        parsed = urlparse(value)
        if value and (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("Use a full http:// or https:// link without credentials")
        return value


class DemoIssueInput(ManualTaskInput):
    project: str = DEMO_PATH


@app.post("/api/issues", status_code=201)
def create_demo_issue(
    body: DemoIssueInput,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task, repo = task_services.create_demo_issue(db, user, body)
    return task_view(task, repo, profile=user.profile, db=db, user=user)


@app.post("/api/tasks/manual", status_code=201)
def create_manual_task(
    body: ManualTaskInput,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task, repo = task_services.create_manual_task(db, user, body)
    return task_view(task, repo, profile=user.profile, db=db, user=user)


@app.get("/api/repositories")
def repositories(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return [
        {
            "id": r.id,
            "path": r.path,
            "source": r.source,
            "last_successful_scan": r.last_success,
            "error": r.scan_error,
        }
        for r in db.scalars(
            select(Repository).where(Repository.enabled.is_(True))
        ).all()
    ]


@app.get("/api/recommendations")
def recommendations(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
    q: str = Query("", max_length=200),
    repository: str = "",
    topic: str = "",
    skill: str = "",
    difficulty: str = "",
    max_effort: float | None = Query(None, ge=0, le=10000),
    status: Literal["open", "closed", "all"] = "open",
    sort: Literal["compatibility", "recency", "difficulty", "effort"] = "compatibility",
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
):
    return discover(
        db,
        user,
        q,
        repository,
        topic,
        skill,
        difficulty,
        max_effort,
        status,
        sort,
        page,
        page_size,
    )


@app.get("/api/tasks/{task_id}")
def task_detail(
    task_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found.")
    return task_view(
        task,
        db.get(Repository, task.repository_id),
        bool(db.get(SavedTask, (user.id, task_id))),
        user.profile,
        db,
        user,
    )


@app.get("/api/me/saved")
def saved_tasks(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    rows = db.execute(
        select(Task, Repository)
        .join(Repository)
        .join(SavedTask, SavedTask.task_id == Task.id)
        .where(SavedTask.user_id == user.id)
        .order_by(SavedTask.saved_at.desc())
    )
    return [task_view(task, repo, True, user.profile, db, user) for task, repo in rows]


@app.put("/api/me/saved/{task_id}", status_code=204)
def save_task(
    task_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found.")
    if task.status != "open":
        raise HTTPException(409, "Only open tasks can be saved.")
    if not db.get(SavedTask, (user.id, task_id)):
        db.add(SavedTask(user_id=user.id, task_id=task_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()  # A concurrent request already saved this task.


@app.delete("/api/me/saved/{task_id}", status_code=204)
def unsave_task(
    task_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    saved = db.get(SavedTask, (user.id, task_id))
    if saved:
        db.delete(saved)
        db.commit()


app.include_router(router)
