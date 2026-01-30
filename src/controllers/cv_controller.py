from helpers.text_normalizer import preprocess_text
from helpers.regex_extractors import (
    extract_email,
    extract_phone,
    extract_gender,
    extract_degree,
 
)

def parse_cv_controller(raw_text: str, lang: str = "en"):
    text = preprocess_text(raw_text, lang, safe=False)

    return {
        "email": extract_email(text),
        "phone": extract_phone(text),
        "gender": extract_gender(text),
        "degree": extract_degree(text),
        
        "clean_text": text
    }
