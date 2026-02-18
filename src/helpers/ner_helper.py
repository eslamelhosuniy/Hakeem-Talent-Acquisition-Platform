def detect_language(text: str):
    """
    Simple Arabic / English detection
    """
    for ch in text:
        if '\u0600' <= ch <= '\u06FF':
            return "ar"
    return "en"


def normalize_label(label: str):
    """
    Make labels unified between Arabic & English models
    """

    mapping = {
        # English spaCy
        "PERSON": "PERSON",
        "ORG": "ORG",
        "GPE": "LOCATION",
        "LOC": "LOCATION",

        # Arabic stanza
        "PER": "PERSON",
        "ORG": "ORG",
        "LOC": "LOCATION"
    }

    return mapping.get(label, label)
