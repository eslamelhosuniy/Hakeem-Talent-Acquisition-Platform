from models.ner_model import extract_entities


def classify_text(text: str):

    try:
        entities = extract_entities(text)

        return {
            "success": True,
            "count": len(entities),
            "entities": entities
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
