import re
from typing import Optional

from helpers.text_normalizer import preprocess_text


def _basic_normalize(text: str) -> str:
    """
    Lightweight normalization tailored for skills and resume chunks.
    Builds on top of preprocess_text(safe=False) to keep behavior consistent.
    """
    if not text:
        return ""

    # Use existing pipeline for unicode, whitespace, casing, and Arabic handling
    text = preprocess_text(text, lang="en", safe=False)

    # Remove most punctuation but keep characters useful for skills (e.g. +, #, .)
    # We'll normalize some of these explicitly in normalize_skill / normalize_text.
    text = re.sub(r"[^\w\+\#\.\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_text(text: Optional[str]) -> str:
    """
    Normalize arbitrary resume text for skill matching.
    """
    if not text:
        return ""

    return _basic_normalize(text)


def normalize_skill(skill: Optional[str]) -> str:
    """
    Normalize skill names and handle common variants:
    - node.js / nodejs / node js
    - c++ / c plus plus
    - c# / c sharp
    """
    if not skill:
        return ""

    text = _basic_normalize(skill)

    # Handle Node.js variants
    text = re.sub(r"\bnode\s*js\b", "node.js", text)
    text = re.sub(r"\bnodejs\b", "node.js", text)

    # Handle C++ variants
    text = re.sub(r"\bc\s*plus\s*plus\b", "c++", text)

    # Handle C# variants
    text = re.sub(r"\bc\s*sharp\b", "c#", text)

    return text

