from fastapi import APIRouter
from pydantic import BaseModel
from ml.resume_enhancer import ResumeEnhancer

router = APIRouter(prefix="/enhancer", tags=["enhancer"])
enhancer = ResumeEnhancer()


class EnhanceRequest(BaseModel):
    resume_text: str
    job_description: str = ""


@router.post("/suggest")
def suggest(req: EnhanceRequest):
    return enhancer.suggest(req.resume_text, req.job_description)