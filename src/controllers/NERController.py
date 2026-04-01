import spacy
import re
from camel_tools.ner import NERecognizer
from camel_tools.tokenizers.word import simple_word_tokenize

class NERController:
    # تحميل موديل spacy (يفضل md أو lg لدقة أفضل)
    nlp = spacy.load("en_core_web_lg")
    
    try:
        arabic_ner = NERecognizer.pretrained()
    except Exception:
        arabic_ner = None

    @staticmethod
    def process_text(text: str):
        is_ar = bool(re.search(r"[\u0600-\u06FF]", text))
        doc = NERController.nlp(text)
        
        results = {
            "name": "Unknown",
            "email": "Not Found",
            "phone": "Not Found",
            "job_title": "Not Specified", 
            "skills": [],               
            "organizations": [],
            "language": "ar" if is_ar else "en"
        }

        # 1. استخراج الإيميل والتليفون أولاً (Regex)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'(\+?\d{10,15})'
        
        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        
        results["email"] = emails[0] if emails else "Not Found"
        results["phone"] = phones[0] if phones else "Not Found"

        # كلمات يجب تجاهلها تماماً من المنظمات والمهارات
        noise_words = [
            "فرع", "دبي", "مصر", "شركة", "أمتلك", "خبرة", "كبيرة", "إلى", "بالإضافة", 
            "الـ", "في", "من", "على", "Contact", "Email", "Phone", "About", "Experience"
        ]

        # 2. استخراج الأسماء والمنظمات (العربي - CamelTools)
        arabic_names = []
        if is_ar and NERController.arabic_ner:
            tokens = simple_word_tokenize(text)
            labels = NERController.arabic_ner.predict([tokens])[0]
            
            for token, label in zip(tokens, labels):
                if label in ['B-PERS', 'I-PERS']:
                    arabic_names.append(token)
                elif label in ['B-ORG', 'I-ORG'] and token not in noise_words:
                    if len(token) > 2:
                        results["organizations"].append(token)
            
            if arabic_names:
                results["name"] = " ".join(arabic_names)

        # 3. استخراج البيانات (الإنجليزي - Spacy)
        english_names = []
        for ent in doc.ents:
            if ent.label_ == "PERSON" and results["name"] == "Unknown":
                english_names.append(ent.text)
            elif ent.label_ == "ORG" and ent.text not in noise_words:
                results["organizations"].append(ent.text)

        if not is_ar and english_names:
            results["name"] = english_names[0]

        # 4. استخراج المسمى الوظيفي والمهارات (Logic-based)
        job_keywords = ["Engineer", "Developer", "Manager", "Analyst", "مهندس", "مطور", "مدير", "محلل", "برمجيات"]
        
        # قائمة "بيضاء" للمهارات التقنية الشائعة لتقليل العشوائية
        tech_whitelist = ["python", "java", "sql", "fastapi", "react", "node", "docker", "aws", "git", "php", "c++"]

        for token in doc:
            word = token.text.strip()
            word_lower = word.lower()

            # أ. المسمى الوظيفي
            if any(j.lower() in word_lower for j in job_keywords) and len(word) > 3:
                if results["job_title"] == "Not Specified":
                    results["job_title"] = word
                elif word not in results["job_title"]:
                    results["job_title"] += f" {word}"

            # ب. المهارات (تحسين الفلترة)
            # الشروط: ليس اسم الشخص، ليس إيميل، ليس منظمة، ليس كلمة ضوضاء
            if (token.pos_ in ["PROPN", "NOUN"]) and (word not in noise_words):
                if word in results["name"] or word in results["email"] or word in results["organizations"]:
                    continue
                
                # إضافة المهارة لو كانت في الـ whitelist أو لو الموديل ملقهاش تصنيف شخص/منظمة
                if word_lower in tech_whitelist or (len(word) > 2 and not token.ent_type_):
                    if not any(char in word for char in ['@', '.', '+']): # منع الإيميلات والرموز
                        results["skills"].append(word)

        # 5. تنظيف وتكرار
        results["skills"] = list(dict.fromkeys(results["skills"]))[:15] # زيادة العدد قليلاً
        results["organizations"] = list(dict.fromkeys(results["organizations"]))
        
        # فلترة أخيرة للمنظمات: لو الكلمة جزء من الاسم متبقاش منظمة
        results["organizations"] = [o for o in results["organizations"] if o not in results["name"] and o not in noise_words]

        return results