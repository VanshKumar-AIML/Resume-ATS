"""
routes/resume_routes.py
------------------------
Core pipeline endpoints, covering workflow steps 2-9:

    POST /resumes/upload          - upload PDF/DOCX, extract text, run analysis
    POST /resumes/analyze-text    - analyze a resume built from scratch (no file)
    GET  /resumes/{id}            - fetch one resume + its analysis
    GET  /resumes/{id}/download   - generate & download the polished PDF
"""

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user
from file_extractor import extract_text, UnsupportedFileTypeError
from pdf_generator import generate_resume_pdf

from ml.keyword_extractor import extract_all
from ml.similarity import compute_match
from ml.predictor import predict_score

router = APIRouter(prefix="/resumes", tags=["resumes"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
GENERATED_DIR = os.path.join(UPLOAD_DIR, "generated")


def _run_analysis_and_save(
    db: Session, user: models.User, raw_text: str,
    job_description: str = None, filename: str = None,
) -> models.Resume:
    """
    Shared logic for both the upload and analyze-text endpoints:
    extract sections/skills, run the ATS + similarity models, persist
    a new Resume version + AnalysisResult.
    """
    extracted = extract_all(raw_text)

    prediction = predict_score(raw_text, job_description)

    match_percentage = None
    matched_keywords, missing_keywords = [], []
    if job_description:
        match_report = compute_match(raw_text, job_description)
        match_percentage = match_report["match_percentage"]
        matched_keywords = match_report["matched_keywords"]
        missing_keywords = match_report["missing_keywords"]

    # Determine next version number for this user
    last_version = (
        db.query(models.Resume)
        .filter(models.Resume.owner_id == user.id)
        .order_by(models.Resume.version.desc())
        .first()
    )
    next_version = (last_version.version + 1) if last_version else 1

    resume = models.Resume(
        owner_id=user.id,
        version=next_version,
        filename=filename,
        raw_text=raw_text,
        sections=extracted["sections"],
        job_description=job_description,
    )
    db.add(resume)
    db.flush()  # get resume.id before creating the analysis row

    analysis = models.AnalysisResult(
        resume_id=resume.id,
        ats_score=prediction["ats_score"],
        match_percentage=match_percentage,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        skills_found=extracted["skills"],
        feature_vector=prediction["feature_vector"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/upload", response_model=schemas.ResumeOut)
def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Workflow steps 2-7: upload -> extract text -> NLP -> ATS score -> JD match."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".docx"):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx files are supported")

    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        raw_text = extract_text(saved_path)
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract any text from the uploaded file")

    resume = _run_analysis_and_save(db, user, raw_text, job_description, filename=file.filename)
    return resume


@router.post("/analyze-text", response_model=schemas.ResumeOut)
def analyze_text(
    payload: schemas.AnalyzeTextRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """For resumes built from scratch in the UI rather than uploaded."""
    resume = _run_analysis_and_save(db, user, payload.resume_text, payload.job_description)
    return resume


@router.get("/{resume_id}", response_model=schemas.ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    resume = (
        db.query(models.Resume)
        .filter(models.Resume.id == resume_id, models.Resume.owner_id == user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get("/{resume_id}/download")
def download_resume(resume_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Workflow step 9: download the optimized resume as a formatted PDF."""
    resume = (
        db.query(models.Resume)
        .filter(models.Resume.id == resume_id, models.Resume.owner_id == user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    os.makedirs(GENERATED_DIR, exist_ok=True)
    output_path = os.path.join(GENERATED_DIR, f"resume_{resume.id}_v{resume.version}.pdf")

    sections = resume.sections or {}
    generate_resume_pdf(
        output_path=output_path,
        full_name=user.full_name or user.email,
        contact_line=user.email,
        sections=sections,
    )

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"resume_v{resume.version}.pdf",
    )
