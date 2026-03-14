from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from controllers.CVController import CVController

router = APIRouter(prefix="/cv", tags=["CV Parser"])

class CVRequest(BaseModel):
    text: str
    lang: str = "en"

@router.post("/parse")
def parse_cv_endpoint(payload: CVRequest):
    controller = CVController()
    is_success, signal, data = controller.parse_cv(
        raw_text=payload.text,
        lang=payload.lang
    )
    if is_success:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"signal": signal, "data": data}
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"signal": signal, "error": data}
    )
