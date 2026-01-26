from pydantic import BaseModel, Field
from typing import List, Dict


class MatchRequest(BaseModel):
    job_description: str = Field(..., min_length=10)
    job_skills: List[str] = Field(default_factory=list)
    cv_text: str = Field(..., min_length=10)


class MatchResponse(BaseModel):
    similarity_score: float
    skill_overlap: List[str]
    implicit_skills: List[str]
    keyword_importance: Dict[str, float]
    model_version: str

