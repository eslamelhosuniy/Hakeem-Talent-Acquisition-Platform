import json
import logging
import os
import re
import warnings
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Tuple

import numpy as np
from rapidfuzz import fuzz  # type: ignore

from helpers.config import get_settings
from utils.nlp.normalize import normalize_text, normalize_skill as normalize_skill_text

if TYPE_CHECKING:
    from openai import OpenAI
    from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SKILLS_PATH = os.path.join(BASE_DIR, "utils", "skills", "linkedin_skills.json")
SEMANTIC_MODEL_NAME = "all-MiniLM-L6-v2"
SEMANTIC_CACHE_DIR = os.path.join(BASE_DIR, ".cache", "huggingface")
DEFAULT_FUZZY_THRESHOLD = 85.0
DEFAULT_SEMANTIC_THRESHOLD = 60.0
DEFAULT_FINAL_THRESHOLD = 60.0


logger = logging.getLogger(__name__)


def normalize_skill(skill: str) -> str:
    return str(skill).lower().strip()


@lru_cache(maxsize=1)
def _load_skills() -> List[str]:
    if not os.path.exists(SKILLS_PATH):
        logger.warning("Skills lexicon file not found at %s.", SKILLS_PATH)
        return []

    with open(SKILLS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure we always return a list of strings
    return [str(s).strip() for s in data if str(s).strip()]


def _cache_hits(func: Any) -> int:
    cache_info = getattr(func, "cache_info", None)
    if not callable(cache_info):
        return 0

    try:
        hits = getattr(cache_info(), "hits", 0)
        return hits if isinstance(hits, int) else 0
    except Exception:
        return 0


def _configure_semantic_cache() -> None:
    os.makedirs(SEMANTIC_CACHE_DIR, exist_ok=True)
    os.environ.setdefault("HF_HOME", SEMANTIC_CACHE_DIR)
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", SEMANTIC_CACHE_DIR)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


@lru_cache(maxsize=1)
def _normalized_skill_variants() -> Tuple[Dict[str, str], List[str]]:
    """
    Returns:
        variant_to_canonical: mapping from normalized variant -> canonical skill
        canonical_list: list of canonical skill names
    """
    skills = _load_skills()

    variant_to_canonical: Dict[str, str] = {}

    # Built-in manual variants for tricky skills
    manual_variants = {
        "Node.js": ["node js", "nodejs", "node.js"],
        "C++": ["c++", "c plus plus"],
        "C#": ["c#", "c sharp"],
    }

    for canonical in skills:
        norm_canonical = normalize_skill_text(canonical)
        if norm_canonical:
            variant_to_canonical[norm_canonical] = canonical

        # Attach manual variants where relevant
        if canonical in manual_variants:
            for v in manual_variants[canonical]:
                norm_v = normalize_skill_text(v)
                if norm_v:
                    variant_to_canonical[norm_v] = canonical

    return variant_to_canonical, skills


@lru_cache(maxsize=1)
def get_embedding_model() -> "SentenceTransformer | None":
    _configure_semantic_cache()

    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        logger.warning(
            "sentence_transformers is unavailable. Semantic matching will fall back to fuzzy-only behavior."
        )
        return None

    try:
        _configure_semantic_cache()
        logger.info(
            "Loading semantic model '%s' from local cache '%s'.",
            SEMANTIC_MODEL_NAME,
            SEMANTIC_CACHE_DIR,
        )
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="`resume_download` is deprecated.*",
                category=FutureWarning,
            )
            model = SentenceTransformer(
                SEMANTIC_MODEL_NAME,
                cache_folder=SEMANTIC_CACHE_DIR,
            )
        logger.info("Semantic model loaded successfully")
        return model
    except Exception as exc:
        logger.warning(
            "Semantic model '%s' was not available in the local cache (%s). Falling back to fuzzy matching.",
            SEMANTIC_MODEL_NAME,
            exc,
        )
        return None


def get_model() -> "SentenceTransformer | None":
    return get_embedding_model()


get_model.cache_clear = get_embedding_model.cache_clear  # type: ignore[attr-defined]
get_model.cache_info = get_embedding_model.cache_info  # type: ignore[attr-defined]


@lru_cache(maxsize=1)
def get_skill_embeddings() -> Tuple[Tuple[str, ...], Any]:
    skills = tuple(_load_skills())
    model_cache_before = _cache_hits(get_embedding_model)
    model = get_embedding_model()
    model_cache_after = _cache_hits(get_embedding_model)
    if model_cache_after > model_cache_before:
        logger.debug("Reusing cached semantic model.")
    if model is None or not skills:
        if not skills:
            logger.warning("No skills available for semantic embedding cache.")
        return skills, None

    try:
        embeddings = model.encode(
            list(skills),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        if getattr(embeddings, "ndim", 0) != 2:
            embeddings = np.atleast_2d(embeddings)
        logger.info(
            "Cached semantic embeddings for %s skills.",
            len(skills),
        )
        return skills, embeddings
    except Exception:
        logger.exception(
            "Failed to build cached skill embeddings. Semantic matching will be skipped."
        )
        return skills, None


@lru_cache(maxsize=1)
def _skill_embedding_index() -> Dict[str, int]:
    skills, _ = get_skill_embeddings()
    index_map: Dict[str, int] = {}

    for idx, skill in enumerate(skills):
        normalized = normalize_skill_text(skill) or normalize_text(skill)
        if normalized:
            index_map[normalized] = idx

    return index_map


def split_text(text: str) -> List[str]:
    if not text:
        return []

    chunks: List[str] = []
    seen = set()

    def add_chunk(value: str) -> None:
        chunk = normalize_text(value)
        if len(chunk) < 2 or chunk in seen:
            return
        seen.add(chunk)
        chunks.append(chunk)

    for part in re.split(r"[\r\n]+|[.!?;:]+", text):
        add_chunk(part)

    if not chunks:
        add_chunk(text)

    return chunks


def _select_skill_embeddings(skills_list: Sequence[str]) -> Tuple[List[str], Any]:
    if not skills_list:
        return [], None

    cache_before = _cache_hits(get_skill_embeddings)
    _, cached_embeddings = get_skill_embeddings()
    cache_after = _cache_hits(get_skill_embeddings)
    if cache_after > cache_before:
        logger.debug("Reusing cached skill embeddings.")

    if cached_embeddings is None:
        logger.info(
            "Semantic embedding cache is unavailable. Falling back to fuzzy-only matching."
        )
        return [], None

    skill_index_map = _skill_embedding_index()
    variant_to_canonical, _ = _normalized_skill_variants()

    selected_skills: List[str] = []
    selected_indices: List[int] = []
    seen = set()

    for skill in skills_list:
        raw_skill = str(skill).strip()
        if not raw_skill:
            continue

        normalized = normalize_skill_text(raw_skill) or normalize_text(raw_skill)
        canonical = variant_to_canonical.get(normalized, raw_skill)
        canonical_normalized = normalize_skill_text(canonical) or normalize_text(canonical)
        skill_idx = skill_index_map.get(canonical_normalized)

        if skill_idx is None:
            continue
        if canonical in seen:
            continue

        seen.add(canonical)
        selected_skills.append(canonical)
        selected_indices.append(skill_idx)

    if not selected_indices:
        logger.debug("No requested skills were available in the semantic embedding cache.")
        return [], None

    return selected_skills, cached_embeddings[selected_indices]


def _canonicalize_skills(skills_list: Sequence[str]) -> List[str]:
    variant_to_canonical, _ = _normalized_skill_variants()
    canonical_skills: List[str] = []
    seen = set()

    for skill in skills_list:
        raw_skill = str(skill).strip()
        if not raw_skill:
            continue

        normalized = normalize_skill_text(raw_skill) or normalize_text(raw_skill)
        canonical = variant_to_canonical.get(normalized, raw_skill)
        if canonical in seen:
            continue

        seen.add(canonical)
        canonical_skills.append(canonical)

    return canonical_skills


def _fuzzy_similarity_map(
    resume_clean_text: str,
    skills_list: Sequence[str],
    min_score: float = 0.0,
) -> Dict[str, Dict[str, Any]]:
    if not resume_clean_text or not skills_list:
        return {}

    canonical_skills = _canonicalize_skills(skills_list)
    norm_resume = normalize_text(resume_clean_text)
    padded_resume = f" {norm_resume} "

    variant_to_canonical, _ = _normalized_skill_variants()
    allowed_skills = set(canonical_skills)
    scores: Dict[str, Dict[str, Any]] = {}

    for variant_norm, canonical in variant_to_canonical.items():
        if canonical not in allowed_skills or not variant_norm:
            continue

        if f" {variant_norm} " in padded_resume or padded_resume.strip().startswith(
            variant_norm + " "
        ) or padded_resume.strip().endswith(" " + variant_norm):
            scores[canonical] = {
                "score": 100.0,
                "method": "contains",
            }

    for canonical in canonical_skills:
        existing_score = float(scores.get(canonical, {}).get("score", 0.0))
        if existing_score >= 100.0:
            continue

        norm_canonical = normalize_skill_text(canonical)
        if not norm_canonical or len(norm_canonical) < 3:
            continue

        fuzzy_score = float(fuzz.partial_ratio(norm_canonical, norm_resume))
        if fuzzy_score > existing_score:
            scores[canonical] = {
                "score": round(fuzzy_score, 2),
                "method": "fuzzy",
            }

    return {
        skill: details
        for skill, details in scores.items()
        if float(details.get("score", 0.0)) >= min_score
    }


def _semantic_similarity_map(
    text: str,
    skills_list: Sequence[str],
) -> Dict[str, Dict[str, Any]]:
    if not text or not skills_list:
        return {}

    chunks = split_text(text)
    if not chunks:
        return {}

    model = get_embedding_model()
    selected_skills, skill_embeddings = _select_skill_embeddings(skills_list)
    if model is None or skill_embeddings is None or not selected_skills:
        logger.info(
            "Semantic similarity skipped because the model or cached embeddings were unavailable."
        )
        return {}

    try:
        chunk_embeddings = model.encode(
            chunks,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        if getattr(chunk_embeddings, "ndim", 0) != 2:
            chunk_embeddings = np.atleast_2d(chunk_embeddings)
        scores_matrix = np.matmul(chunk_embeddings, skill_embeddings.T)
        logger.info("Using semantic similarity scoring")
    except Exception:
        logger.exception(
            "Semantic similarity computation failed. Falling back to fuzzy-only matching."
        )
        return {}

    if getattr(scores_matrix, "ndim", 0) != 2 or scores_matrix.shape[1] != len(
        selected_skills
    ):
        logger.error(
            "Semantic similarity matrix shape mismatch: got %s for %s skills.",
            tuple(getattr(scores_matrix, "shape", ())),
            len(selected_skills),
        )
        return {}

    max_scores = scores_matrix.max(axis=0)
    best_chunk_indices = scores_matrix.argmax(axis=0)

    results: Dict[str, Dict[str, Any]] = {}
    for idx, canonical in enumerate(selected_skills):
        best_idx = int(best_chunk_indices[idx])
        best_similarity = float(max_scores[idx])
        results[canonical] = {
            "score": round(best_similarity * 100, 2),
            "semantic_score": round(best_similarity, 4),
            "matched_text": chunks[best_idx] if chunks else "",
        }

    return results


def _collapse_debug_entries(entries: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    collapsed: Dict[str, Dict[str, Any]] = {}

    for entry in entries:
        skill = str(entry.get("skill", "")).strip()
        if not skill:
            continue

        current_score = float(entry.get("score", 0))
        existing = collapsed.get(skill)
        if existing is None or current_score > float(existing.get("score", 0)):
            collapsed[skill] = dict(entry)

    return collapsed


def _combine_skill_scores(
    text: str,
    skills_list: Sequence[str],
    fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
    semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
    final_threshold: float = DEFAULT_FINAL_THRESHOLD,
) -> Dict[str, Dict[str, Any]]:
    canonical_skills = _canonicalize_skills(skills_list)
    if not text or not canonical_skills:
        return {}

    semantic_scores = _semantic_similarity_map(text, canonical_skills)
    semantic_available = bool(semantic_scores)
    if semantic_available:
        logger.info("Semantic model scoring is active for combined scoring.")
    else:
        logger.warning("Semantic model unavailable, falling back to fuzzy only")

    fuzzy_scores = _fuzzy_similarity_map(text, canonical_skills, min_score=0.0)

    combined: Dict[str, Dict[str, Any]] = {}
    for skill in canonical_skills:
        fuzzy_entry = fuzzy_scores.get(skill, {})
        semantic_entry = semantic_scores.get(skill, {})

        fuzzy_score = float(fuzzy_entry.get("score", 0.0))
        semantic_score = float(semantic_entry.get("score", 0.0))
        final_score = (
            round((0.4 * fuzzy_score) + (0.6 * semantic_score), 2)
            if semantic_available
            else round(fuzzy_score, 2)
        )
        threshold_met = (
            (
                fuzzy_score >= fuzzy_threshold
                or semantic_score >= semantic_threshold
                or final_score >= final_threshold
            )
            if semantic_available
            else fuzzy_score >= fuzzy_threshold
        )

        method = "fuzzy"
        if semantic_available and semantic_score > 0 and fuzzy_score > 0:
            method = "hybrid"
        elif semantic_score > 0:
            method = "semantic"
        elif fuzzy_entry.get("method") == "contains":
            method = "contains"

        combined[skill] = {
            "skill": skill,
            "method": method,
            "score": final_score,
            "final_score": final_score,
            "fuzzy_score": round(fuzzy_score, 2),
            "semantic_score": round(semantic_score, 2),
            "semantic_similarity": round(semantic_score / 100.0, 4),
            "matched_text": semantic_entry.get("matched_text", ""),
            "semantic_used": semantic_available,
            "passes_threshold": threshold_met,
        }

        if threshold_met or final_score > 0:
            logger.debug(
                "Final score: %s for skill=%s fuzzy=%s semantic=%s",
                final_score,
                skill,
                round(fuzzy_score, 2),
                round(semantic_score, 2),
            )

    return combined


def _shorten_text(text: str, max_chars: int = 500) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def _build_rule_based_explanation(
    matched_skills: List[str],
    missing_skills: List[str],
    score: float,
) -> str:
    if score >= 80:
        strength = "strong"
    elif score >= 50:
        strength = "moderate"
    else:
        strength = "weak"

    top_matched = ", ".join(matched_skills[:3]) if matched_skills else "no clearly aligned skills"
    top_missing = ", ".join(missing_skills[:3]) if missing_skills else "no major skill gaps"

    return (
        f"This candidate is a {strength} match for the role with a score of {score:.1f}. "
        f"Best-aligned skills include {top_matched}. "
        f"Key gaps to review are {top_missing}."
    )


def _resolve_explanation_settings() -> Dict[str, Any]:
    try:
        settings = get_settings()
        return {
            "use_ai_explanation": bool(getattr(settings, "USE_AI_EXPLANATION", False)),
            "openai_api_key": getattr(settings, "OPENAI_API_KEY", "") or "",
            "openai_api_url": getattr(settings, "OPENAI_API_URL", "") or "https://api.openai.com/v1",
            "generation_model_id": getattr(settings, "GENERATION_MODEL_ID", "") or "gpt-4o-mini",
        }
    except Exception:
        use_ai_env = os.getenv("USE_AI_EXPLANATION", "false").strip().lower()
        return {
            "use_ai_explanation": use_ai_env in {"1", "true", "yes", "on"},
            "openai_api_key": os.getenv("OPENAI_API_KEY", "").strip(),
            "openai_api_url": os.getenv("OPENAI_API_URL", "https://api.openai.com/v1").strip(),
            "generation_model_id": os.getenv("GENERATION_MODEL_ID", "gpt-4o-mini").strip(),
        }


@lru_cache(maxsize=1)
def _get_openai_client(api_key: str, api_url: str) -> "OpenAI":
    from openai import OpenAI

    return OpenAI(
        api_key=api_key,
        base_url=api_url or "https://api.openai.com/v1",
    )


def generate_explanation(
    cv_text: str,
    jd_text: str,
    matched_skills: List[str],
    missing_skills: List[str],
    score: float,
) -> str:
    rule_based_explanation = _build_rule_based_explanation(
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        score=score,
    )

    settings = _resolve_explanation_settings()
    if not settings["use_ai_explanation"] or not settings["openai_api_key"]:
        logger.info(
            "Using rule-based explanation because AI explanations are disabled or no OpenAI API key is configured."
        )
        return rule_based_explanation

    try:
        client = _get_openai_client(
            settings["openai_api_key"],
            settings["openai_api_url"],
        )
        model = settings["generation_model_id"] or "gpt-4o-mini"

        cv_summary = _shorten_text(cv_text, max_chars=450)
        jd_summary = _shorten_text(jd_text, max_chars=450)
        matched_summary = ", ".join(matched_skills[:5]) if matched_skills else "None"
        missing_summary = ", ".join(missing_skills[:5]) if missing_skills else "None"

        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=120,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a hiring assistant. Write a concise, professional, recruiter-friendly "
                        "candidate evaluation in 2 to 3 sentences."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Create a short hiring explanation using the details below.\n"
                        f"Score: {score:.1f}\n"
                        f"CV summary: {cv_summary}\n"
                        f"Job description summary: {jd_summary}\n"
                        f"Matched skills: {matched_summary}\n"
                        f"Missing skills: {missing_summary}\n"
                        "Keep it concise, balanced, and useful for recruiters."
                    ),
                },
            ],
        )

        explanation = response.choices[0].message.content if response.choices else None
        explanation_text = (explanation or "").strip()
        return explanation_text or rule_based_explanation
    except Exception:
        logger.exception(
            "AI explanation generation failed. Falling back to rule-based explanation."
        )
        return rule_based_explanation


def match_skills_fuzzy(
    resume_clean_text: str,
    threshold: int = 85,
) -> Dict[str, Any]:
    """
    Match skills from the local LinkedIn-style lexicon against resume text.

    Strategy:
    1) Fast exact 'contains' match against normalized resume text.
    2) Fuzzy match using partial_ratio against the full normalized text.
    3) Deduplicate and sort by score desc.
    """
    if not resume_clean_text:
        return {"skills": [], "debug": []}

    fuzzy_scores = _fuzzy_similarity_map(
        resume_clean_text,
        _load_skills(),
        min_score=float(threshold),
    )

    debug_entries_sorted = sorted(
        (
            {
                "skill": skill,
                "method": details.get("method", "fuzzy"),
                "score": float(details.get("score", 0.0)),
            }
            for skill, details in fuzzy_scores.items()
        ),
        key=lambda d: (-(d.get("score", 0)), d.get("method") != "contains"),
    )

    skills_only = [entry["skill"] for entry in debug_entries_sorted]

    return {
        "skills": skills_only,
        "debug": debug_entries_sorted,
    }


def match_skills_semantic(
    resume_text: str,
    skills_list: List[str],
    threshold: float = 0.6,
) -> Dict[str, Any]:
    semantic_scores = _semantic_similarity_map(resume_text, skills_list)
    if not semantic_scores:
        logger.info(
            "No semantic matches available; returning an empty semantic result set."
        )
        return {"skills": [], "debug": [], "scores": {}, "semantic_scores": {}}

    threshold_score = threshold * 100 if threshold <= 1 else threshold
    matched_entries: List[Dict[str, Any]] = []
    for skill, details in semantic_scores.items():
        if float(details["score"]) < threshold_score:
            continue

        matched_entries.append(
            {
                "skill": skill,
                "method": "semantic",
                "score": float(details["score"]),
                "semantic_score": float(details["score"]),
                "semantic_similarity": float(details["semantic_score"]),
                "final_score": float(details["score"]),
                "matched_text": details["matched_text"],
            }
        )

    matched_entries.sort(
        key=lambda entry: (-float(entry["score"]), entry["skill"].lower())
    )

    return {
        "skills": [entry["skill"] for entry in matched_entries],
        "debug": matched_entries,
        "scores": {entry["skill"]: entry["score"] for entry in matched_entries},
        "semantic_scores": {
            entry["skill"]: entry["semantic_score"] for entry in matched_entries
        },
    }


def match_skills_advanced(resume_text: str) -> Dict[str, Any]:
    skills_list = _load_skills()
    if not resume_text or not skills_list:
        return {
            "skills": [],
            "debug": [],
            "scores": {},
            "semantic_scores": {},
            "fuzzy_scores": {},
        }

    combined_scores = _combine_skill_scores(resume_text, skills_list)
    matched_entries = sorted(
        (
            details
            for details in combined_scores.values()
            if bool(details.get("passes_threshold"))
        ),
        key=lambda entry: (-float(entry.get("final_score", 0)), entry["skill"].lower()),
    )

    return {
        "skills": [entry["skill"] for entry in matched_entries],
        "debug": matched_entries,
        "scores": {
            entry["skill"]: float(entry.get("final_score", 0)) for entry in matched_entries
        },
        "semantic_scores": {
            entry["skill"]: float(entry.get("semantic_score", 0)) for entry in matched_entries
        },
        "fuzzy_scores": {
            entry["skill"]: float(entry.get("fuzzy_score", 0)) for entry in matched_entries
        },
    }


def _build_normalized_skill_map(skills: Sequence[str]) -> Dict[str, str]:
    normalized_map: Dict[str, str] = {}

    for skill in skills:
        original_skill = str(skill).strip()
        normalized_skill = normalize_skill(original_skill)
        if normalized_skill and normalized_skill not in normalized_map:
            normalized_map[normalized_skill] = original_skill

    return normalized_map


def evaluate_candidate(cv_text: str, jd_text: str) -> Dict[str, Any]:
    cv_matches = match_skills_advanced(cv_text)
    jd_matches = match_skills_advanced(jd_text)

    cv_skill_list = list(cv_matches.get("skills", []))
    jd_skill_list = list(jd_matches.get("skills", []))
    jd_skills = set(jd_skill_list)

    if not jd_skills:
        explanation = generate_explanation(
            cv_text=cv_text,
            jd_text=jd_text,
            matched_skills=[],
            missing_skills=[],
            score=0.0,
        )
        return {
            "score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "explanation": explanation,
            "recommendations": [
                "Add clearer skill requirements to the job description so the evaluation can score the candidate accurately."
            ],
        }

    skill_alignment = _combine_skill_scores(cv_text, sorted(jd_skills))

    normalized_extracted = _build_normalized_skill_map(cv_skill_list)
    normalized_job = _build_normalized_skill_map(jd_skill_list)
    normalized_matched_keys: List[str] = []
    matched_skills: List[str] = []
    missing_skills: List[str] = []

    logger.debug("Normalized extracted skills: %s", sorted(normalized_extracted.keys()))
    logger.debug("Normalized job skills: %s", sorted(normalized_job.keys()))

    for normalized_job_skill, original_job_skill in normalized_job.items():
        alignment_entry = skill_alignment.get(original_job_skill, {})
        passes_alignment = (
            float(alignment_entry.get("final_score", 0.0)) >= DEFAULT_FINAL_THRESHOLD
            or not alignment_entry.get("semantic_used", True)
        )

        if normalized_job_skill in normalized_extracted and passes_alignment:
            normalized_matched_keys.append(normalized_job_skill)
            matched_skills.append(original_job_skill)
        else:
            missing_skills.append(original_job_skill)

    logger.debug("Matched normalized skills: %s", normalized_matched_keys)

    skill_ratio = len(matched_skills) / len(jd_skills)

    scoring_components = []
    semantic_used = False
    for skill in jd_skills:
        details = skill_alignment.get(skill, {})
        scoring_components.append(float(details.get("final_score", 0.0)) / 100.0)
        semantic_used = semantic_used or bool(details.get("semantic_used", False))

    if not semantic_used:
        logger.info(
            "Semantic scoring unavailable during candidate evaluation. Falling back to fuzzy-only final scores."
        )
    semantic_avg = sum(scoring_components) / len(jd_skills)

    score = round((skill_ratio * 0.6 + semantic_avg * 0.4) * 100, 2)
    logger.debug(
        "Candidate evaluation scoring -> skill_ratio=%s semantic_avg=%s final_score=%s",
        round(skill_ratio, 4),
        round(semantic_avg, 4),
        score,
    )

    recommendations: List[str] = []
    if missing_skills:
        recommendations.append(
            "Add clearer evidence for these job skills: " + ", ".join(missing_skills[:10])
        )
    if skill_ratio < 0.5:
        recommendations.append(
            "Align the CV language more closely with the job description so required skills are easier to detect."
        )
    if semantic_avg < 0.6:
        recommendations.append(
            "Strengthen project descriptions with outcomes, tools, and responsibilities that show direct fit for the role."
        )
    if not recommendations:
        recommendations.append(
            "The CV aligns well with the job description; keep the strongest matching skills and achievements prominent."
        )

    explanation = generate_explanation(
        cv_text=cv_text,
        jd_text=jd_text,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        score=score,
    )

    return {
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "explanation": explanation,
        "recommendations": recommendations,
    }

