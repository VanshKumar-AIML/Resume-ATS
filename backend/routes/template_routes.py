import json, os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any
# from backend.pdf_generator import generate_pdf_from_template  # wire to your existing generator

router = APIRouter(prefix="/templates", tags=["templates"])
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


@router.get("")
def list_templates():
    out = []
    for fn in os.listdir(TEMPLATE_DIR):
        if fn.endswith(".json"):
            with open(os.path.join(TEMPLATE_DIR, fn), encoding="utf-8") as f:
                data = json.load(f)
            out.append({"id": fn[:-5], **data})
    return out


@router.get("/{template_id}")
def get_template(template_id: str):
    path = os.path.join(TEMPLATE_DIR, f"{template_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "Template not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class RenderRequest(BaseModel):
    resume: Dict[str, Any]


@router.post("/{template_id}/render")
def render(template_id: str, req: RenderRequest):
    path = os.path.join(TEMPLATE_DIR, f"{template_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "Template not found")
    # Replace with a call into your existing pdf_generator that accepts
    # (template, resume_data) and returns a file path.
    # pdf_path = generate_pdf_from_template(path, req.resume)
    # return FileResponse(pdf_path, media_type="application/pdf")
    raise HTTPException(501, "Wire render() to your pdf_generator implementation")