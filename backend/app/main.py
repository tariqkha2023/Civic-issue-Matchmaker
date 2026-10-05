from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.task_storage import create_tasks_table, get_tasks
from app.database import get_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Civic Issue Matchmaker backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check():
    conn = get_connection()
    conn.close()

    return {"database": "ok"}

@app.get("/tasks")
def list_tasks():
    create_tasks_table()
    return get_tasks()