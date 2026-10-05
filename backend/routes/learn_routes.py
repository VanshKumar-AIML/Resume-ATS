from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ml.certificate_recommender import CertificateRecommender
from ml.study_material import StudyMaterialRecommender
from ml.keyword_extractor import extract_skills  # adjust import to match your code

router = APIRouter(prefix="/learn", tags=["learn"])
cert_rec = CertificateRecommender()
mat_rec = StudyMaterialRecommender()


class LearnRequest(BaseModel):
    resume_text: str
    resume_skills: Optional[List[str]] = None
    cost: str = "any"
    free_only: bool = False
    max_cost: Optional[float] = None
    level: Optional[str] = None
    platforms: Optional[List[str]] = None
    providers: Optional[List[str]] = None
    max_hours: Optional[float] = None
    top_k: int = 20


@router.post("/certificates")
def certificates(req: LearnRequest):
    skills = req.resume_skills or extract_skills(req.resume_text)
    return {
        "skills_used": skills,
        "results": cert_rec.recommend(
            resume_skills=skills,
            resume_text=req.resume_text,
            free_only=req.free_only,
            max_cost=req.max_cost,
            level=req.level,
            providers=req.providers,
            top_k=req.top_k,
        ),
    }


@router.post("/materials")
def materials(req: LearnRequest):
    skills = req.resume_skills or extract_skills(req.resume_text)
    return {
        "skills_used": skills,
        "results": mat_rec.recommend(
            resume_skills=skills,
            resume_text=req.resume_text,
            cost=req.cost,
            platforms=req.platforms,
            level=req.level,
            max_hours=req.max_hours,
            top_k=req.top_k,
        ),
    }