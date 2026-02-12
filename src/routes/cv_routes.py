from fastapi import APIRouter
from pydantic import BaseModel
from controllers.cv_controller import parse_cv_controller

router = APIRouter(prefix="/cv", tags=["CV Parser"])

class CVRequest(BaseModel):
    text: str
    lang: str = "en"

@router.post("/parse")
def parse_cv_endpoint(payload: CVRequest):
    return parse_cv_controller(
        raw_text=payload.text,
        lang=payload.lang
    )
