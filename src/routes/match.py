from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.skill_match_service import evaluate_candidate


router = APIRouter(prefix="/match", tags=["Candidate Evaluation"])


class CandidateEvaluationRequest(BaseModel):
    cv_text: str = Field(..., description="Raw or cleaned candidate CV text")
    job_description: str = Field(..., description="Target job description text")


@router.post("/evaluate")
def evaluate_candidate_endpoint(payload: CandidateEvaluationRequest):
    return evaluate_candidate(
        cv_text=payload.cv_text,
        jd_text=payload.job_description,
    )
