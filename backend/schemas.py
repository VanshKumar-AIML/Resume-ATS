"""
schemas.py
----------
Pydantic models for request validation and response serialization.
"""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Resume analysis
# ---------------------------------------------------------------------------

class AnalyzeTextRequest(BaseModel):
    """Used when the resume is built from scratch (no file upload)."""
    resume_text: str
    job_description: Optional[str] = None


class AnalysisOut(BaseModel):
    ats_score: float
    match_percentage: Optional[float] = None
    matched_keywords: Optional[List[str]] = []
    missing_keywords: Optional[List[str]] = []
    skills_found: Optional[List[str]] = []

    model_config = {"from_attributes": True}


class ResumeOut(BaseModel):
    id: int
    version: int
    filename: Optional[str]
    sections: Optional[Dict]
    created_at: datetime
    analysis: Optional[AnalysisOut]

    model_config = {"from_attributes": True}


class ResumeHistoryOut(BaseModel):
    """Lightweight version for the dashboard's version-history list."""
    id: int
    version: int
    ats_score: Optional[float]
    match_percentage: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}
