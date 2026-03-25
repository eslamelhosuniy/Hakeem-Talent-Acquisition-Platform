from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from controllers.SkillMatchingController import SkillMatchingController

router = APIRouter(prefix="/skills", tags=["Skill Matching"])

class SkillMatchRequest(BaseModel):
    resume_text: str = Field(..., description="Clean text extracted from CV PDF")
    job_text: str = Field(..., description="Job Description text")
    lang: str = "en"
    threshold: float = 0.55

@router.post("/match")
def match_skills_endpoint(payload: SkillMatchRequest):
    controller = SkillMatchingController()
    is_success, signal, result = controller.skill_match(
        resume_text=payload.resume_text,
        job_text=payload.job_text,
        lang=payload.lang,
        sim_threshold=payload.threshold,
    )
    if is_success:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"signal": signal, "data": result}
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"signal": signal, "error": result}
    )
