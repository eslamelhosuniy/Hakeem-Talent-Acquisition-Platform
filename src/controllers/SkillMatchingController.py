from __future__ import annotations

import os
import re
from typing import List, Dict, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz, process

from controllers.BaseController import BaseController
from helpers.text_normalizer import preprocess_text
from models.enums.ResponseEnums import ResponseSignal


# Load model once (important for performance)
_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


class SkillMatchingController(BaseController):
    # Cache lexicon once at class level
    _LEXICON: Optional[List[str]] = None
    _LEXICON_NORM_MAP: Optional[Dict[str, str]] = None

    def __init__(self):
        super().__init__()
        self.skills_path = os.path.join(self.files_dir, "all_linkedin_skills.txt")

    # ---------------------------
    # Utils
    # ---------------------------

    def _normalize_text(self, s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"[\u200f\u200e]", "", s)
        s = re.sub(r"\s+", " ", s)
        return s

    def _load_lexicon(self) -> List[str]:
        if SkillMatchingController._LEXICON is not None:
            return SkillMatchingController._LEXICON

        if not os.path.exists(self.skills_path):
            raise FileNotFoundError(
                f"Skills file not found at: {self.skills_path}. "
                f"Put all_linkedin_skills.txt under src/assets/files/"
            )

        seen = set()
        skills: List[str] = []
        with open(self.skills_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                raw = line.strip()
                if not raw:
                    continue
                key = self._normalize_text(raw)
                if key in seen:
                    continue
                seen.add(key)
                skills.append(raw)

        SkillMatchingController._LEXICON = skills
        SkillMatchingController._LEXICON_NORM_MAP = { self._normalize_text(s): s for s in skills }
        return skills

    def _build_aliases(self) -> Dict[str, List[str]]:
        return {
            "javascript": ["js", "java script"],
            "typescript": ["ts", "type script"],
            "node.js": ["node", "nodejs"],
            "react": ["reactjs", "react.js"],
            "next.js": ["nextjs", "next"],
            "postgresql": ["postgres", "postgre"],
            "mongodb": ["mongo", "mongo db"],
            "machine learning": ["ml"],
            "natural language processing": ["nlp"],
        }

    def _add_alias_hits(self, text: str, hits: set, lexicon_norm_map: Dict[str, str]) -> None:
        t = self._normalize_text(text)
        for canonical, alias_list in self._build_aliases().items():
            for a in alias_list:
                if re.search(rf"\b{re.escape(self._normalize_text(a))}\b", t):
                    c_norm = self._normalize_text(canonical)
                    if c_norm in lexicon_norm_map:
                        hits.add(lexicon_norm_map[c_norm])

    def _extract_skills_lexicon(self, text: str, lexicon: List[str], max_ngram_words: int = 5) -> List[str]:
        if not text:
            return []

        t = self._normalize_text(text)
        lexicon_norm_map = SkillMatchingController._LEXICON_NORM_MAP or { self._normalize_text(s): s for s in lexicon }

        hits = set()
        tokens = set(re.findall(r"[a-z0-9\+\#\.\-]+", t))
        for s in lexicon:
            s_norm = self._normalize_text(s)
            if len(s_norm.split()) > max_ngram_words:
                continue

            first = s_norm.split()[0]
            if first not in tokens:
                continue

            pattern = r"(?:^|[^a-z0-9])" + re.escape(s_norm) + r"(?:$|[^a-z0-9])"
            if re.search(pattern, t):
                hits.add(s)

        self._add_alias_hits(text, hits, lexicon_norm_map)
        return sorted(hits, key=lambda x: x.lower())

    def _embed(self, items: List[str]) -> np.ndarray:
        if not items:
            return np.zeros((0, 384), dtype=np.float32)
        emb = _MODEL.encode(items, normalize_embeddings=True)
        return np.array(emb, dtype=np.float32)

    def _cosine_matrix(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        if a.size == 0 or b.size == 0:
            return np.zeros((a.shape[0], b.shape[0]), dtype=np.float32)
        return a @ b.T  # normalized => dot = cosine

    # ---------------------------
    # Main Method
    # ---------------------------

    def skill_match(self, resume_text: str, job_text: str, lang: str = "en", sim_threshold: float = 0.55):
        try:
            lexicon = self._load_lexicon()

            # Normalize & clean using existing helper (same pattern as cv_controller)
            resume_clean = preprocess_text(resume_text, lang, safe=False)
            job_clean = preprocess_text(job_text, lang, safe=False)

            resume_skills = self._extract_skills_lexicon(resume_clean, lexicon)
            job_skills = self._extract_skills_lexicon(job_clean, lexicon)

            res_emb = self._embed(resume_skills)
            job_emb = self._embed(job_skills)
            sim = self._cosine_matrix(job_emb, res_emb)  # [job, resume]

            matched = []
            missing = []
            used_resume = set()

            for i, jskill in enumerate(job_skills):
                if sim.shape[1] == 0:
                    missing.append(jskill)
                    continue

                row = sim[i]
                best_idx = int(np.argmax(row))
                best_sim = float(row[best_idx])

                if best_sim >= sim_threshold:
                    matched.append({"skill": jskill, "similarity": round(best_sim, 4)})
                    used_resume.add(resume_skills[best_idx])
                else:
                    missing.append(jskill)

            # Overall score = average best matches over job skills (missing => 0)
            best_sims = np.zeros((len(job_skills),), dtype=np.float32)
            for m in matched:
                idx = job_skills.index(m["skill"])
                best_sims[idx] = m["similarity"]

            overall = float(best_sims.mean()) if len(job_skills) else 0.0

            extra_resume_skills = [s for s in resume_skills if s not in used_resume]
            matched_sorted = sorted(matched, key=lambda x: x["similarity"], reverse=True)

            data = {
                "overall_score": round(overall, 4),
                "threshold": sim_threshold,
                "job_skills": job_skills,
                "resume_skills": resume_skills,
                "matched": matched_sorted,
                "missing_job_skills": missing,
                "extra_resume_skills": extra_resume_skills,
            }
            
            return True, ResponseSignal.SKILL_MATCHING_SUCCESS.value, data
            
        except Exception as e:
            return False, ResponseSignal.SKILL_MATCHING_ERROR.value, str(e)
