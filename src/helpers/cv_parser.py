from text_normalizer import preprocess_text
from regex_extractors import *


def parse_cv(raw_text, lang="en"):
    text = preprocess_text(raw_text, lang,safe=False)

    return {
        "email": extract_email(text),
        "phone": extract_phone(text),
        "gender": extract_gender(text),
        "degree": extract_degree(text), 
        "clean_text": text
    }
