import sys
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer, util

sys.path.insert(0, str(Path(__file__).parent.parent))

from .models import MatchRequest, MatchResponse
from common.embeddings import get_model
from common.text_clean import clean_text, extract_keywords_tfidf, extract_skills_dictionary


class SemanticMatchService:
    def __init__(self, model_name: str | None = None) -> None:
        self.model: SentenceTransformer = get_model(model_name)
        self.model_version: str = self.model.__class__.__name__ + ":" + (model_name or "default")

    def match(self, req: MatchRequest) -> MatchResponse:
        job_text = clean_text(req.job_description + "\nSkills: " + ", ".join(req.job_skills))
        cv_text = clean_text(req.cv_text)

        job_emb = self.model.encode(job_text, convert_to_tensor=True)
        cv_emb = self.model.encode(cv_text, convert_to_tensor=True)
        similarity = util.cos_sim(job_emb, cv_emb).item()

        job_skill_phrases = extract_skills_dictionary(job_text)
        cv_skill_phrases = extract_skills_dictionary(cv_text)
        overlap: List[str] = sorted(set(job_skill_phrases).intersection(cv_skill_phrases))

        keyword_importance = extract_keywords_tfidf(job_text, cv_text)
        implicit_skills = [s for s in cv_skill_phrases if s not in overlap][:10]

        return MatchResponse(
            similarity_score=round(similarity * 100, 2),
            skill_overlap=overlap[:10],
            implicit_skills=implicit_skills,
            keyword_importance=keyword_importance,
            model_version=self.model_version,
        )

