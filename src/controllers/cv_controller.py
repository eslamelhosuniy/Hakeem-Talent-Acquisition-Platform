from helpers.text_normalizer import preprocess_text
from helpers.regex_extractors import (
    extract_email,
    extract_phone,
    extract_gender,
    extract_degree,
)
from services.skill_match_service import match_skills_fuzzy


def parse_cv_controller(raw_text: str, lang: str = "en"):
    text = preprocess_text(raw_text, lang, safe=False)

    skills_result = match_skills_fuzzy(text, threshold=85)
    skills = skills_result.get("skills", [])
    debug_entries = skills_result.get("debug", [])

    return {
        "email": extract_email(text),
        "phone": extract_phone(text),
        "gender": extract_gender(text),
        "degree": extract_degree(text),
        "clean_text": text,
        "extracted_skills": skills,
        "skills_debug": debug_entries[:30],
        "text_preview": text[:500],
    }
