from enum import Enum

class ResponseSignal(Enum):
    # Standard responses
    SUCCESS = "success"
    ERROR = "error"
    INVALID_REQUEST = "invalid_request"
    
    # CV Parsing
    CV_PARSING_SUCCESS = "cv_parsing_success"
    CV_PARSING_ERROR = "cv_parsing_error"
    
    # NER Extraction
    NER_EXTRACTION_SUCCESS = "ner_extraction_success"
    NER_EXTRACTION_ERROR = "ner_extraction_error"
    
    # Skill Matching
    SKILL_MATCHING_SUCCESS = "skill_matching_success"
    SKILL_MATCHING_ERROR = "skill_matching_error"

    # Analysis
    ANALYSIS_SUCCESS = "analysis_success"
    ANALYSIS_ERROR = "analysis_error"
