import spacy
import re
import stanza
import logging
from spacy.pipeline import EntityRuler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


BLACKSET = {"نص", "تحميل", "السيرة الذاتية", "CV", "Resume", "Page"}

class NERController:
    _nlp_en = None
    _nlp_ar = None

    def __init__(self):
       
        if NERController._nlp_en is None:
            self._initialize_en_model()
        if NERController._nlp_ar is None:
            self._initialize_ar_model()

    @classmethod
    def _initialize_en_model(cls):
        try:
            logger.info("Loading English Model (en_core_web_lg)...")
            cls._nlp_en = spacy.load("en_core_web_lg")
            
            
            if "entity_ruler" not in cls._nlp_en.pipe_names:
                ruler = cls._nlp_en.add_pipe("entity_ruler", before="ner")
                patterns = [
                    # الوظائف الإنجليزية
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "software", "OP": "?"}, {"LOWER": "engineer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "full"}, {"LOWER": "stack"}, {"LOWER": "developer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "frontend"}, {"LOWER": "developer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "backend"}, {"LOWER": "developer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "data"}, {"LOWER": "analyst"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "project"}, {"LOWER": "manager"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "accountant"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "designer"}]},

                    
                    {"label": "SKILL", "pattern": [{"LOWER": "python"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "fastapi"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "react"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "sql"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "machine"}, {"LOWER": "learning"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "data"}, {"LOWER": "analysis"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "project"}, {"LOWER": "management"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "accounting"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "design"}]},

                ]
                ruler.add_patterns(patterns)
        except Exception as e:
            logger.error(f"Error loading English model: {e}")
            cls._nlp_en = spacy.load("en_core_web_sm")

    @classmethod
    def _initialize_ar_model(cls):
        try:
            logger.info("Loading Arabic Model (Stanza)...")
            cls._nlp_ar = stanza.Pipeline("ar", processors='tokenize,ner', use_gpu=False, verbose=False)
        except Exception as e:
            logger.error(f"Error loading Arabic model: {e}")

    def _is_arabic(self, text):
        return bool(re.search(r"[\u0600-\u06FF]", text))

    def _normalize_label(self, label):
        label_map = {
            "PERSON": "person", "PER": "person",
            "ORG": "organization", "GPE": "location",
            "LOC": "location", "JOB_TITLE": "job_title",
            "SKILL": "skills", # ده اللي بيخليها تروح لعمود المهارات
            "FAC": "facility"
        }
        return label_map.get(label, label.lower())

    def extract_entities(self, text: str):
        # القائمة الكاملة للوظائف العربي اللي كانت عندك
        AR_JOB_KEYWORDS = {
            "مهندس", "محاسب", "مطور", "مبرمج", "مدير", "محلل", "مصمم", "فني",
            "مشرف", "مسؤول", "مستشار", "مدرب", "محامي", "طبيب", "معلم",
            "باحث", "كاتب", "صحفي", "مترجم", "فنان", "موسيقي", "مهندس برمجيات"
            ,"مهندس بيانات", "مهندس شبكات", "مهندس نظم", "مهندس أمن", "مهندس ذكاء اصطناعي",
            "مهندس تعلم آلي", "مهندس روبوتات", "مهندس إلكترونيات", "مهندس ميكانيكا",
            "مهندس كهرباء", "مهندس مدني", "مهندس معماري", "مهندس صناعي", "مهندس بيئة",
            "مهندس طيران", "مهندس فضاء", "مهندس بحري", "مهندس زراعي", "مهندس غذاء",
            "مهندس نفط", "مهندس غاز", "مهندس طاقة", "مهندس صوت", "مهندس فيديو",
            "مهندس جودة", "مهندس صيانة", "مهندس دعم فني", "مهندس مبيعات", "مهندس تسويق",
            "مهندس موارد بشرية", "مهندس مالي", "مهندس قانوني", "مهندس صحي", "مهندس تعليمي",
            "مهندس أبحاث", "مهندس تطوير أعمال", "مهندس علاقات عامة", "مهندس لوجستي",
            "مهندس إنتاج", "مهندس تخطيط", "مهندس استشارات", "مهندس تدريب", "مهندس توظيف", "مهندس خدمات العملاء", "مهندس أمن معلومات",
            "مهندس بيانات كبيرة", "مهندس سحابة", "مهندس إنترنت الأشياء", "مهندس واقع افتراضي",
            "مهندس واقع معزز", "مهندس بلوكتشين", "مهندس عملات رقمية", "مهندس تكنولوجيا مالية",
            "مهندس رعاية صحية", "مهندس تعليم إلكتروني", "مهندس ألعاب", "مهندس ترفيه", "مهندس سفر وسياحة", "مهندس ضيافة", "مهندس رياضي", "مهندس إعلامي",
            "مهندس بيئي", "مهندس زراعي", "مهندس غذائي", "مهندس نفطي", "مهندس غازي",
            "مهندس طاقة متجددة", "مهندس طاقة نووية", "مهندس طاقة شمسية", "مهندس طاقة رياح", "مهندس طاقة مائية", "مهندس طاقة حرارية",
            "مهندس طاقة حيوية", "مهندس طاقة جيوحرارية", "مهندس طاقة مد والجزر", "مهندس طاقة موجية", "مهندس طاقة كهرومائية",
            "مهندس طاقة نووية صغيرة", "مهندس طاقة نووية كبيرة", "مهندس طاقة نووية متنقلة", "مهندس طاقة نووية ثابتة",
            "مهندس طاقة نووية متجددة", "مهندس طاقة نووية غير متجددة", "مهندس طاقة نووية هجينة", "مهندس طاقة نووية تقليدية",
            "مهندس طاقة نووية مستقبلية", "مهندس طاقة نووية مستدامة", "مهندس طاقة نووية متطورة", "مهندس طاقة نووية مبتكرة",
            "مهندس طاقة نووية تقليدية", "مهندس طاقة نووية مستقبلية", "مهندس طاقة نووية مستدامة", "مهندس طاقة نووية متطورة", "مهندس طاقة نووية مبتكرة",

        }

        try:
            if not text or len(text.strip()) < 2:
                return False, "text_too_short", "Text is too short"

            language = "ar" if self._is_arabic(text) else "en"
            
            
            raw_entities = {
                "email": list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))),
                "phone": list(set(re.findall(r'(\+?\d{10,15})', text)))
            }

            if language == "ar" and self._nlp_ar:
                doc = self._nlp_ar(text)
                for sent in doc.sentences:
                    for ent in sent.ents:
                        label = self._normalize_label(ent.type)
                        val = ent.text.strip()
                        if val not in BLACKSET:
                            if label not in raw_entities: raw_entities[label] = []
                            if val not in raw_entities[label]: raw_entities[label].append(val)
                
             
                for keyword in AR_JOB_KEYWORDS:
                    if keyword in text:
                        if "job_title" not in raw_entities: raw_entities["job_title"] = []
                        if keyword not in raw_entities["job_title"]: raw_entities["job_title"].append(keyword)

            else: # English
                if self._nlp_en:
                    doc = self._nlp_en(text)
                    for ent in doc.ents:
                        label = self._normalize_label(ent.label_)
                        val = ent.text.strip()
                        if val not in BLACKSET:
                            if label not in raw_entities: raw_entities[label] = []
                            if val not in raw_entities[label]: raw_entities[label].append(val)

           
            final_entities = {k: v for k, v in raw_entities.items() if v}
            
            result = {
                "language": language,
                "entities": final_entities,
                "total_entities": sum(len(v) for v in final_entities.values())
            }
            return True, "success", result

        except Exception as e:
            logger.error(f"Critical NER Error: {e}")
            return False, "system_error", str(e)