from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from controllers.cv_controller import parse_cv_controller
from helpers.pdf_extractor import extract_text_from_pdf_bytes


router = APIRouter(prefix="/cv", tags=["CV Parser"])


class CVRequest(BaseModel):
    text: str
    lang: str = "en"


@router.post("/parse")
def parse_cv_endpoint(payload: CVRequest):
    return parse_cv_controller(
        raw_text=payload.text,
        lang=payload.lang,
    )


@router.post("/parse-file")
async def parse_cv_file_endpoint(
    file: UploadFile = File(...),
    lang: str = "en",
):
    """
    PDF resume upload endpoint.
    Extracts text from the uploaded PDF, preprocesses it,
    and reuses the existing CV parsing controller.
    """
    data = await file.read()
    raw_text = extract_text_from_pdf_bytes(data)

    return parse_cv_controller(
        raw_text=raw_text,
        lang=lang,
    )

