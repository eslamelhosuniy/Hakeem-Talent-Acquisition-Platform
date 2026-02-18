import spacy

from helpers.ner_helper import detect_language, normalize_label


nlp_en = None
nlp_ar = None


def load_english():
    global nlp_en
    if nlp_en is None:
        nlp_en = spacy.load("en_core_web_sm")
    return nlp_en


def load_arabic():
    global nlp_ar

    if nlp_ar is None:
        import stanza   # ← هنا الحل المهم
        nlp_ar = stanza.Pipeline(lang="ar", processors="tokenize,ner")

    return nlp_ar


def extract_entities(text: str):

    lang = detect_language(text)
    entities = []

    if lang == "en":
        nlp = load_english()
        doc = nlp(text)

        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": normalize_label(ent.label_),
                "language": "english"
            })

    else:
        nlp = load_arabic()
        doc = nlp(text)

        for sentence in doc.sentences:
            for ent in sentence.ents:
                entities.append({
                    "text": ent.text,
                    "label": normalize_label(ent.type),
                    "language": "arabic"
                })

    return entities
