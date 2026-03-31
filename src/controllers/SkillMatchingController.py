from __future__ import annotations

import logging
from typing import Dict, List

from controllers.BaseController import BaseController
from helpers.text_normalizer import preprocess_text
from models.enums.ResponseEnums import ResponseSignal
from services.skill_match_service import (
    _combine_skill_scores,
    match_skills_advanced,
)


logger = logging.getLogger(__name__)


class SkillMatchingController(BaseController):
    def skill_match(
        self,
        resume_text: str,
        job_text: str,
        lang: str = "en",
        sim_threshold: float = 0.55,
    ):
        try:
            resume_clean = preprocess_text(resume_text, lang, safe=False)
            job_clean = preprocess_text(job_text, lang, safe=False)

            resume_result = match_skills_advanced(resume_clean)
            job_result = match_skills_advanced(job_clean)

            resume_skills = resume_result.get("skills", [])
            job_skills = job_result.get("skills", [])
            resume_skill_set = set(resume_skills)

            combined_scores = _combine_skill_scores(resume_clean, job_skills)
            semantic_available = any(
                bool(details.get("semantic_used", False))
                for details in combined_scores.values()
            )
            if not semantic_available:
                logger.info(
                    "SkillMatchingController falling back to non-semantic matching for /skills/match."
                )

            matched: List[Dict[str, float | str]] = []
            missing: List[str] = []

            for job_skill in job_skills:
                score_details = combined_scores.get(job_skill, {})
                final_score = float(score_details.get("final_score", 0.0)) / 100.0

                if job_skill in resume_skill_set and final_score > 0:
                    similarity = final_score
                    matched.append(
                        {"skill": job_skill, "similarity": round(similarity, 4)}
                    )
                elif final_score >= sim_threshold:
                    matched.append(
                        {"skill": job_skill, "similarity": round(final_score, 4)}
                    )
                else:
                    missing.append(job_skill)

            overall = (
                round(
                    sum(float(item["similarity"]) for item in matched) / len(job_skills),
                    4,
                )
                if job_skills
                else 0.0
            )

            matched_skill_names = {str(item["skill"]) for item in matched}
            extra_resume_skills = [
                skill for skill in resume_skills if skill not in matched_skill_names
            ]

            data = {
                "overall_score": overall,
                "threshold": sim_threshold,
                "job_skills": job_skills,
                "resume_skills": resume_skills,
                "matched": sorted(
                    matched,
                    key=lambda item: float(item["similarity"]),
                    reverse=True,
                ),
                "missing_job_skills": missing,
                "extra_resume_skills": extra_resume_skills,
            }

            return True, ResponseSignal.SKILL_MATCHING_SUCCESS.value, data
        except Exception as exc:
            logger.exception("Skill matching controller failed.")
            return False, ResponseSignal.SKILL_MATCHING_ERROR.value, str(exc)
