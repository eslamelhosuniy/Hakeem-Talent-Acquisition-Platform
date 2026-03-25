import json
import os
from functools import lru_cache
from typing import Any, Dict, List, Tuple

from rapidfuzz import fuzz  # type: ignore

from utils.nlp.normalize import normalize_text, normalize_skill


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SKILLS_PATH = os.path.join(BASE_DIR, "utils", "skills", "linkedin_skills.json")


@lru_cache(maxsize=1)
def _load_skills() -> List[str]:
    if not os.path.exists(SKILLS_PATH):
        return []

    with open(SKILLS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure we always return a list of strings
    return [str(s).strip() for s in data if str(s).strip()]


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
        norm_canonical = normalize_skill(canonical)
        if norm_canonical:
            variant_to_canonical[norm_canonical] = canonical

        # Attach manual variants where relevant
        if canonical in manual_variants:
            for v in manual_variants[canonical]:
                norm_v = normalize_skill(v)
                if norm_v:
                    variant_to_canonical[norm_v] = canonical

    return variant_to_canonical, skills


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

    norm_resume = normalize_text(resume_clean_text)

    variant_to_canonical, canonical_skills = _normalized_skill_variants()

    found_scores: Dict[str, float] = {}
    debug_entries: List[Dict[str, Any]] = []

    padded_resume = f" {norm_resume} "

    # 1) Exact / contains matches on normalized variants
    for variant_norm, canonical in variant_to_canonical.items():
        if not variant_norm:
            continue

        # Match whole words or phrases
        if f" {variant_norm} " in padded_resume or padded_resume.strip().startswith(
            variant_norm + " "
        ) or padded_resume.strip().endswith(" " + variant_norm):
            score = 100.0
            # Keep highest score if already found
            if found_scores.get(canonical, 0) < score:
                found_scores[canonical] = score

            debug_entries.append(
                {
                    "skill": canonical,
                    "method": "contains",
                    "score": score,
                }
            )

    # 2) Fuzzy matching using partial_ratio for the full text
    for canonical in canonical_skills:
        # Skip if we already have a perfect contains match
        if found_scores.get(canonical, 0) >= 100:
            continue

        norm_canonical = normalize_skill(canonical)
        if not norm_canonical:
            continue

        score = float(fuzz.partial_ratio(norm_canonical, norm_resume))
        if score >= threshold:
            if score > found_scores.get(canonical, 0):
                found_scores[canonical] = score

            debug_entries.append(
                {
                    "skill": canonical,
                    "method": "fuzzy",
                    "score": score,
                }
            )

    # 3) Deduplicate and sort
    # Keep max score per skill
    skills_with_scores = sorted(
        found_scores.items(), key=lambda kv: kv[1], reverse=True
    )

    skills_only = [name for name, _ in skills_with_scores]

    # Sort debug entries by score desc and then by method (contains before fuzzy)
    debug_entries_sorted = sorted(
        debug_entries,
        key=lambda d: (-(d.get("score", 0)), d.get("method") != "contains"),
    )

    return {
        "skills": skills_only,
        "debug": debug_entries_sorted,
    }

