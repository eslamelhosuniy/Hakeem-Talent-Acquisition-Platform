import re
import unicodedata


# Normalize text
def normalize_text(text: str) -> str:
    if not text:
        return ""

    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # remove control chars فقط
    text = re.sub(r"[\x00-\x08\x0B-\x1F\x7F]", " ", text)

    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# Normalize arabic
def normalize_arabic(text: str) -> str:
    return re.sub(
        r"[إأآا]", "ا",
        re.sub(r"[ىي]", "ي",
        re.sub(r"[ؤ]", "و",
        re.sub(r"[ئ]", "ي",
        re.sub(r"[ة]", "ه", text)))))



# Normalize arabic numbers
def normalize_arabic_numbers(text: str) -> str:
    return text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))


# Preprocess
def preprocess_text(text: str, lang="en", safe=True):
    """
    safe=True  -> for extraction (email, phone, dates)
    safe=False -> for NLP / skills
    """

    text = normalize_text(text)

    if lang == "ar":
        text = normalize_arabic_numbers(text)
        text = normalize_arabic(text)

    if not safe:
        text = text.lower()

    return text

