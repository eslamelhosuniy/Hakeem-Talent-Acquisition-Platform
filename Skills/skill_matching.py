from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Optional

import numpy as np
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer


# ---------------------------
# Utilities
# ---------------------------

def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[\u200f\u200e]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def load_skill_lexicon(path: str) -> List[str]:
    """
    Reads a newline-separated skills file.
    Keeps unique, non-empty skills (normalized uniqueness but preserves original).
    """
    seen = set()
    skills = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            key = normalize_text(raw)
            if key in seen:
                continue
            seen.add(key)
            skills.append(raw)
    return skills


def build_aliases() -> Dict[str, List[str]]:
    """
    Optional: common aliases / abbreviations that appear in CV/JD text.
    Expand over time.
    """
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


def add_alias_hits(text: str, hits: set, lexicon_norm_map: Dict[str, str]) -> None:
    t = normalize_text(text)
    aliases = build_aliases()
    for canonical, alias_list in aliases.items():
        for a in alias_list:
            if re.search(rf"\b{re.escape(normalize_text(a))}\b", t):
                c_norm = normalize_text(canonical)
                if c_norm in lexicon_norm_map:
                    hits.add(lexicon_norm_map[c_norm])


# ---------------------------
# Extraction (Lexicon-based)
# ---------------------------

def extract_skills_lexicon(
    text: str,
    lexicon: List[str],
    *,
    max_ngram_words: int = 5,
) -> List[str]:
    """
    Lexicon matching by boundary-ish substring search + optional aliases.
    Works decently with big skill lists.
    """
    if not text:
        return []

    t = normalize_text(text)
    lexicon_norm_map = {normalize_text(s): s for s in lexicon}

    hits = set()

    # token prefilter
    tokens = set(re.findall(r"[a-z0-9\+\#\.\-]+", t))
    for s in lexicon:
        s_norm = normalize_text(s)

        if len(s_norm.split()) > max_ngram_words:
            continue

        first = s_norm.split()[0]
        if first not in tokens:
            continue

        # relaxed boundary search
        pattern = r"(?:^|[^a-z0-9])" + re.escape(s_norm) + r"(?:$|[^a-z0-9])"
        if re.search(pattern, t):
            hits.add(s)

    add_alias_hits(text, hits, lexicon_norm_map)

    return sorted(hits, key=lambda x: x.lower())


def map_to_lexicon_fuzzy(
    candidates: List[str],
    lexicon: List[str],
    *,
    threshold: int = 90,
    limit_per_item: int = 1,
) -> List[str]:
    """
    Optional: map extracted phrases to closest LinkedIn skill label via fuzzy matching.
    """
    if not candidates:
        return []

    lex = [normalize_text(s) for s in lexicon]
    norm_to_original = {normalize_text(s): s for s in lexicon}

    mapped = set()
    for c in candidates:
        c_norm = normalize_text(c)
        match = process.extract(
            c_norm,
            lex,
            scorer=fuzz.token_set_ratio,
            limit=limit_per_item
        )
        if match and match[0][1] >= threshold:
            mapped.add(norm_to_original[match[0][0]])

    return sorted(mapped, key=lambda x: x.lower())


# ---------------------------
# Semantic Matching + Scoring
# ---------------------------

@dataclass
class SkillMatch:
    skill: str
    similarity: float


@dataclass
class MatchResult:
    overall_score: float
    matched: List[SkillMatch]
    missing_job_skills: List[str]
    extra_resume_skills: List[str]
    resume_skills: List[str]
    job_skills: List[str]


class SemanticSkillMatcher:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def _embed(self, items: List[str]) -> np.ndarray:
        if not items:
            # all-MiniLM-L6-v2 -> 384 dims
            return np.zeros((0, 384), dtype=np.float32)
        emb = self.model.encode(items, normalize_embeddings=True)
        return np.array(emb, dtype=np.float32)

    @staticmethod
    def _cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        # normalized embeddings => cosine = dot product
        if a.size == 0 or b.size == 0:
            return np.zeros((a.shape[0], b.shape[0]), dtype=np.float32)
        return a @ b.T

    def match(
        self,
        resume_skills: List[str],
        job_skills: List[str],
        *,
        sim_threshold: float = 0.55,
        weights: Optional[Dict[str, float]] = None,
    ) -> MatchResult:
        """
        For each job skill, find best semantic match among resume skills.
        overall_score = weighted average of best similarities for job skills (missing => 0).
        """
        weights = weights or {}
        job_w = np.array([float(weights.get(s, 1.0)) for s in job_skills], dtype=np.float32)

        res_emb = self._embed(resume_skills)
        job_emb = self._embed(job_skills)
        sim = self._cosine_matrix(job_emb, res_emb)  # [job, resume]

        matched: List[SkillMatch] = []
        missing: List[str] = []
        used_resume = set()

        for i, jskill in enumerate(job_skills):
            if sim.shape[1] == 0:
                missing.append(jskill)
                continue

            row = sim[i]
            best_idx = int(np.argmax(row))
            best_sim = float(row[best_idx])

            if best_sim >= sim_threshold:
                matched.append(SkillMatch(skill=jskill, similarity=best_sim))
                used_resume.add(resume_skills[best_idx])
            else:
                missing.append(jskill)

        best_sims = np.zeros((len(job_skills),), dtype=np.float32)
        for m in matched:
            idx = job_skills.index(m.skill)
            best_sims[idx] = m.similarity

        denom = float(job_w.sum()) if float(job_w.sum()) > 0 else 1.0
        overall = float((best_sims * job_w).sum() / denom)

        extra = [s for s in resume_skills if s not in used_resume]
        matched_sorted = sorted(matched, key=lambda x: x.similarity, reverse=True)

        return MatchResult(
            overall_score=overall,
            matched=matched_sorted,
            missing_job_skills=missing,
            extra_resume_skills=extra,
            resume_skills=resume_skills,
            job_skills=job_skills,
        )


def run_skill_matching(
    resume_text: str,
    job_text: str,
    skills_file_path: str,
    *,
    sim_threshold: float = 0.55,
) -> MatchResult:
    """
    One-stop helper:
    - Load LinkedIn skills lexicon
    - Extract skills from resume & job text
    - Semantic match + overall score
    """
    lexicon = load_skill_lexicon(skills_file_path)

    resume_skills = extract_skills_lexicon(resume_text, lexicon)
    job_skills = extract_skills_lexicon(job_text, lexicon)

    matcher = SemanticSkillMatcher()
    return matcher.match(resume_skills, job_skills, sim_threshold=sim_threshold)


def pretty_print(result: MatchResult, max_items: int = 30) -> None:
    print(f"Overall score: {result.overall_score:.3f}")
    print("\nJob skills extracted:", ", ".join(result.job_skills[:max_items]))
    print("\nResume skills extracted:", ", ".join(result.resume_skills[:max_items]))

    print("\nMatched job skills:")
    for m in result.matched[:max_items]:
        print(f"- {m.skill} (sim={m.similarity:.3f})")

    print("\nMissing job skills:")
    for s in result.missing_job_skills[:max_items]:
        print(f"- {s}")

    print("\nExtra resume skills (not used in matching):")
    for s in result.extra_resume_skills[:max_items]:
        print(f"- {s}")


if __name__ == "__main__":
    # Quick demo test
    SKILLS_PATH = "all_linkedin_skills.txt"

    resume_text = """
    Backend developer with experience in Python, Flask, PostgreSQL, MongoDB, Docker, and REST APIs.
    Built ML projects using NLP and transformers. Familiar with Git and CI/CD.
    """

    job_text = """
    We are hiring a Backend Engineer. Required: Python, Flask, REST API, PostgreSQL, Docker, Git.
    Nice to have: NLP, Machine Learning, CI/CD, Kubernetes.
    """

    result = run_skill_matching(resume_text, job_text, SKILLS_PATH, sim_threshold=0.55)
    pretty_print(result)
