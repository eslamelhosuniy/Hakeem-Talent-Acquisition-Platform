from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

from docx import Document

from controllers.cv_controller import parse_cv_controller
from helpers.pdf_extractor import extract_text_from_pdf_bytes
from services.skill_match_service import evaluate_candidate, match_skills_advanced


SUPPORTED_UPLOAD_EXTENSIONS = {".pdf", ".docx"}


def _extract_text_from_docx_bytes(data: bytes) -> str:
    if not data:
        return ""

    document = Document(BytesIO(data))
    parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(parts)


def extract_text_from_upload(filename: str, data: bytes) -> str:
    extension = ""
    if filename and "." in filename:
        extension = "." + filename.rsplit(".", 1)[-1].lower()

    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")

    if extension == ".pdf":
        return extract_text_from_pdf_bytes(data)

    return _extract_text_from_docx_bytes(data)


def analyze_candidate_profile(
    cv_text: str,
    job_description: str,
    lang: str = "en",
) -> Dict[str, Any]:
    parsed_cv = parse_cv_controller(raw_text=cv_text, lang=lang)
    clean_text = parsed_cv.get("clean_text", "")

    skills_result = match_skills_advanced(clean_text)
    evaluation_result = evaluate_candidate(clean_text, job_description)

    entities = {
        "email": parsed_cv.get("email"),
        "phone": parsed_cv.get("phone"),
        "gender": parsed_cv.get("gender"),
        "degree": parsed_cv.get("degree"),
    }

    return {
        "parsed_cv": {
            "clean_text": clean_text,
            "entities": entities,
        },
        "skills": {
            "extracted": skills_result.get("skills", []),
            "matched": evaluation_result.get("matched_skills", []),
            "missing": evaluation_result.get("missing_skills", []),
        },
        "score": evaluation_result.get("score", 0.0),
        "explanation": evaluation_result.get("explanation", ""),
        "recommendations": evaluation_result.get("recommendations", []),
    }
