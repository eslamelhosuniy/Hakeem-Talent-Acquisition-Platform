from fastapi import APIRouter, Depends
from pydantic import BaseModel

from helpers.config import get_settings, Settings
from helpers.text_normalizer import preprocess_text
from services.skill_match_service import match_skills_fuzzy


main_router = APIRouter()
base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)


@main_router.get("/")
async def root(app_settings: Settings = Depends(get_settings)):
    return {
        f"Welcome to the {app_settings.APP_NAME} Platform API {app_settings.APP_VERSION}"
    }


@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    return {
        "app_name": app_settings.APP_NAME,
        "app_version": app_settings.APP_VERSION,
    }


class SkillsTestRequest(BaseModel):
    text: str
    lang: str = "en"


@main_router.post("/debug/skills-test")
async def skills_test(payload: SkillsTestRequest):
    """
    Debug endpoint to validate skill matching with arbitrary text.
    """
    clean_text = preprocess_text(payload.text, payload.lang, safe=False)
    skills_result = match_skills_fuzzy(clean_text, threshold=85)

    skills = skills_result.get("skills", [])
    debug_entries = skills_result.get("debug", [])

    return {
        "extracted_skills": skills,
        "skills_debug": debug_entries[:30],
        "text_preview": clean_text[:500],
    }


