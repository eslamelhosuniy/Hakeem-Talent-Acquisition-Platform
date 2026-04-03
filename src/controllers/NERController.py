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
            # تم التعديل للنسخة sm لضمان العمل على Vercel وبسرعة عالية
            logger.info("Loading English Model (en_core_web_sm)...")
            cls._nlp_en = spacy.load("en_core_web_sm")
            
            # إضافة الـ EntityRuler لتحسين الأداء ليكون مماثل للنسخة lg في الكلمات المفتاحية
            if "entity_ruler" not in cls._nlp_en.pipe_names:
                ruler = cls._nlp_en.add_pipe("entity_ruler", before="ner")
                patterns = [
                    # وظائف برمجية وتقنية
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "software"}, {"LOWER": "engineer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "full"}, {"LOWER": "stack"}, {"LOWER": "developer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "frontend"}, {"LOWER": "developer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "backend"}, {"LOWER": "developer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "data"}, {"LOWER": "analyst"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "project"}, {"LOWER": "manager"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "accountant"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "designer"}]},
                    {"label": "JOB_TITLE", "pattern": [{"LOWER": "ui/ux"}, {"LOWER": "designer"}]},

                    # مهارات تقنية (تقوية الـ sm)
                    {"label": "SKILL", "pattern": [{"LOWER": "python"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "fastapi"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "react"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "sql"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "machine"}, {"LOWER": "learning"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "deep"}, {"LOWER": "learning"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "docker"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "kubernetes"}]},
                    {"label": "SKILL", "pattern": [{"LOWER": "git"}]},
                ]
                ruler.add_patterns(patterns)
        except Exception as e:
            logger.error(f"Error loading English model: {e}")
            # محاولة أخيرة في حالة فشل التحميل تماماً
            cls._nlp_en = None

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
            "SKILL": "skills", 
            "FAC": "facility"
        }
        return label_map.get(label, label.lower())

    def extract_entities(self, text: str):
        AR_JOB_KEYWORDS = {
            "مهندس", "محاسب", "مطور", "مبرمج", "مدير", "محلل", "مصمم", "فني",
            "مشرف", "مسؤول", "مستشار", "مدرب", "محامي", "طبيب", "معلم",
            "باحث", "كاتب", "صحفي", "مترجم", "فنان", "موسيقي", "مهندس برمجيات"
            , "مهندس بيانات", "مهندس تعلم آلي", "مهندس ذكاء اصطناعي", "مهندس نظم",
            "مهندس شبكات", "مهندس أمن سيبراني", "محلل بيانات", "محلل نظم", "محلل أعمال",
            "مدير مشروع", "مدير تقنية المعلومات", "مدير تطوير الأعمال", "محاسب قانوني",
            "محاسب إداري", "محاسب مالي", "مطور ويب", "مطور تطبيقات", "مطور ألعاب",
            "مصمم جرافيك", "مصمم واجهات المستخدم", "فني دعم", "فني صيانة", "مشرف إنتاج",
            "مسؤول موارد بشرية", "مستشار قانوني", "مدرب رياضي", "محامي جنائي", "طبيب عام",
            "معلم لغة", "باحث علمي", "كاتب محتوى", "صحفي تحقيقات", "مترجم فوري", "فنان تشكيلي",
            "موسيقي محترف"
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

            else: # English (Using sm model with Ruler)
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