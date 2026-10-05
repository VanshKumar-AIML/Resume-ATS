"""
main.py
-------
FastAPI application entrypoint.

Run with:
    cd backend
    uvicorn main:app --reload --port 8000

This makes the project root (one level up) importable so `ml/` can be
imported as a regular package from the route files.
"""

import os
import sys

# Make the project root (Resume-ATS/) importable so `ml.*` resolves correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models  # noqa: F401 (ensures models are registered before create_all)
from routes import auth_routes, resume_routes, dashboard_routes

# Create tables on startup if they don't exist yet.
# For production, replace this with proper Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Resume Builder & ATS Score Predictor",
    description="Analyzes resumes, predicts ATS compatibility, and suggests improvements.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(resume_routes.router)
app.include_router(dashboard_routes.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
