import spacy

# Load English model
nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    """Extract named entities from text"""
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_
        })
    return entities
