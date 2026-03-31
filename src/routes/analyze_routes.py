from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import JSONResponse

from models.enums.ResponseEnums import ResponseSignal
from services.analysis_service import analyze_candidate_profile, extract_text_from_upload


router = APIRouter(prefix="", tags=["Analysis"])


JSON_REQUEST_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "cv_text": {
            "type": "string",
            "description": "Raw CV or resume text.",
        },
        "job_description": {
            "type": "string",
            "description": "Target job description text.",
        },
    },
    "required": ["cv_text", "job_description"],
}


MULTIPART_REQUEST_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file": {
            "type": "string",
            "format": "binary",
            "description": "PDF or DOCX resume file.",
        },
        "cv_text": {
            "type": "string",
            "description": "Optional raw CV text when not uploading a file.",
        },
        "job_description": {
            "type": "string",
            "description": "Target job description text.",
        },
    },
    "required": ["job_description"],
}


@router.post(
    "/analyze",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": JSON_REQUEST_SCHEMA},
                "multipart/form-data": {"schema": MULTIPART_REQUEST_SCHEMA},
            },
        }
    },
)
async def analyze_endpoint(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    cv_text: Optional[str] = Form(default=None),
    job_description: Optional[str] = Form(default=None),
):
    try:
        request_cv_text = cv_text
        request_job_description = job_description

        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await request.json()
            if not isinstance(payload, dict):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.ANALYSIS_ERROR.value,
                        "error": "Invalid JSON payload.",
                    },
                )

            request_cv_text = str(payload.get("cv_text") or "").strip()
            request_job_description = str(payload.get("job_description") or "").strip()
        else:
            request_cv_text = (request_cv_text or "").strip()
            request_job_description = (request_job_description or "").strip()

        if not request_job_description:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "signal": ResponseSignal.ANALYSIS_ERROR.value,
                    "error": "job_description is required.",
                },
            )

        if file is not None:
            file_bytes = await file.read()
            if not file_bytes:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.ANALYSIS_ERROR.value,
                        "error": "Uploaded file is empty.",
                    },
                )

            try:
                request_cv_text = extract_text_from_upload(file.filename or "", file_bytes).strip()
            except ValueError as exc:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.ANALYSIS_ERROR.value,
                        "error": str(exc),
                    },
                )

        if not request_cv_text:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.ANALYSIS_ERROR.value,
                    "error": "cv_text is required when no file is uploaded, and extracted CV text cannot be empty.",
                },
            )

        analysis_result = analyze_candidate_profile(
            cv_text=request_cv_text,
            job_description=request_job_description,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.ANALYSIS_SUCCESS.value,
                "data": analysis_result,
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.ANALYSIS_ERROR.value,
                "error": str(exc),
            },
        )
