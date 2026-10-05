"""
routes/dashboard_routes.py
----------------------------
GET /dashboard/history - list all resume versions + scores for the logged-in
                          user, so the frontend can chart improvement over time.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/history", response_model=List[schemas.ResumeHistoryOut])
def get_history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    resumes = (
        db.query(models.Resume)
        .options(joinedload(models.Resume.analysis))
        .filter(models.Resume.owner_id == user.id)
        .order_by(models.Resume.version.asc())
        .all()
    )

    return [
        schemas.ResumeHistoryOut(
            id=r.id,
            version=r.version,
            ats_score=r.analysis.ats_score if r.analysis else None,
            match_percentage=r.analysis.match_percentage if r.analysis else None,
            created_at=r.created_at,
        )
        for r in resumes
    ]
