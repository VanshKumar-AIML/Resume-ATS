"""
models.py
---------
SQLAlchemy ORM models: User, Resume (versions), AnalysisResult.

Mirrors database/schema.sql — keep the two in sync if you edit one.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="owner", cascade="all, delete-orphan")


class Resume(Base):
    """
    A single resume version belonging to a user. Every re-upload or rebuild
    creates a new row so the dashboard can show improvement over versions.
    """
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1)
    filename = Column(String, nullable=True)          # original uploaded filename, if any
    raw_text = Column(Text, nullable=False)            # extracted plain text
    sections = Column(JSON, nullable=True)             # {"skills": "...", "experience": "...", ...}
    job_description = Column(Text, nullable=True)      # JD pasted by user, if any
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="resumes")
    analysis = relationship("AnalysisResult", back_populates="resume", uselist=False, cascade="all, delete-orphan")


class AnalysisResult(Base):
    """
    ML output for a given resume version: ATS score, JD match %, keyword gaps.
    One-to-one with Resume.
    """
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False, unique=True)

    ats_score = Column(Float, nullable=False)
    match_percentage = Column(Float, nullable=True)     # null if no JD was provided
    matched_keywords = Column(JSON, nullable=True)
    missing_keywords = Column(JSON, nullable=True)
    skills_found = Column(JSON, nullable=True)
    feature_vector = Column(JSON, nullable=True)        # for explainability in the UI
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="analysis")
