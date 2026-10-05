from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from ml.profile_parser import ProfileParser, merge_profiles

router = APIRouter(prefix="/profile", tags=["profile"])
parser = ProfileParser()


class ImportRequest(BaseModel):
    urls: List[str]


@router.post("/import")
def import_profile(req: ImportRequest):
    if not req.urls:
        raise HTTPException(400, "Provide at least one URL")
    parsed = [parser.parse(u) for u in req.urls]
    merged = merge_profiles(parsed)
    return {"profile": merged, "raw": parsed}