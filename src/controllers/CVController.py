from controllers.BaseController import BaseController
from helpers.text_normalizer import preprocess_text
from helpers.regex_extractors import (
    extract_email,
    extract_phone,
    extract_gender,
    extract_degree,
)
from models.enums.ResponseEnums import ResponseSignal

class CVController(BaseController):
    def __init__(self):
        super().__init__()

    def parse_cv(self, raw_text: str, lang: str = "en"):
        text = preprocess_text(raw_text, lang, safe=False)

        data = {
            "email": extract_email(text),
            "phone": extract_phone(text),
            "gender": extract_gender(text),
            "degree": extract_degree(text),
            "clean_text": text
        }
        
        return True, ResponseSignal.CV_PARSING_SUCCESS.value, data
