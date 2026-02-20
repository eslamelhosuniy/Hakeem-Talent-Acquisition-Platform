import spacy
import re


class NERController:

    def __init__(self):
        # Multilingual model (English + Arabic)
        self.nlp = spacy.load("xx_ent_wiki_sm")

    # -----------------------
    # Detect Arabic
    # -----------------------
    def _is_arabic(self, text):
        return bool(re.search(r"[\u0600-\u06FF]", text))

    # -----------------------
    # Normalize Labels
    # -----------------------
    def _normalize_label(self, label):

        label_map = {
            "PERSON": "person",
            "PER": "person",

            "ORG": "organization",
            "GPE": "location",
            "LOC": "location",

            "DATE": "date",
            "TIME": "time",

            "NORP": "nationality",
            "FAC": "facility",

            "WORK_OF_ART": "work",
            "EVENT": "event",
            "PRODUCT": "product",
            "LAW": "law",
            "LANGUAGE": "language",
            "MONEY": "money",
            "PERCENT": "percent",
            "QUANTITY": "quantity",
            "CARDINAL": "number",
        }

        return label_map.get(label, label.lower())

    # -----------------------
    # Extract Entities
    # -----------------------
    def extract_entities(self, text: str):

        doc = self.nlp(text)

        # Detect language just for response
        language = "ar" if self._is_arabic(text) else "en"

        entities = {}

        for ent in doc.ents:
            label = self._normalize_label(ent.label_)

            if label not in entities:
                entities[label] = []

            if ent.text not in entities[label]:
                entities[label].append(ent.text)

        return {
            "language": language,
            "entities": entities,
            "total_entities": sum(len(v) for v in entities.values())
        }