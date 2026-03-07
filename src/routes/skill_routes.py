from fastapi import APIRouter
from pydantic import BaseModel, Field

from controllers.skill_matching_ import skill_match_controller

router = APIRouter(prefix="/skills", tags=["Skill Matching"])


class SkillMatchRequest(BaseModel):
    resume_text: str = Field(..., description="Clean text extracted from CV PDF")
    job_text: str = Field(..., description="Job Description text")
    lang: str = "en"
    threshold: float = 0.55


@router.post("/match")
def match_skills_endpoint(payload: SkillMatchRequest):
    return skill_match_controller(
        resume_text=payload.resume_text,
        job_text=payload.job_text,
        lang=payload.lang,
        sim_threshold=payload.threshold,
    )
