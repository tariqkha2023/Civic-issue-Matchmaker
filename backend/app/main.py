from app.database import get_connection
from fastapi import FastAPI

app = FastAPI()


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