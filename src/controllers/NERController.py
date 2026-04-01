import spacy
import re
from camel_tools.ner import NERecognizer
from camel_tools.tokenizers.word import simple_word_tokenize

class NERController:
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

        results["email"] = next(iter(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)), "Not Found")
        results["phone"] = next(iter(re.findall(r'(\+?\d{10,15})', text)), "Not Found")

        
        noise_words = ["فرع", "دبي", "مصر", "شركة", "أمتلك", "خبرة", "كبيرة", "إلى", "بالإضافة", "الـ", "في"]
        
        
        if is_ar and NERController.arabic_ner:
            tokens = simple_word_tokenize(text)
            labels = NERController.arabic_ner.predict([tokens])[0]
            
            full_name_parts = []
            for token, label in zip(tokens, labels):
                if label in ['B-PERS', 'I-PERS']:
                    full_name_parts.append(token)
                elif label in ['B-ORG', 'I-ORG'] and token not in noise_words:
                   
                    results["organizations"].append(token)
            
            if full_name_parts:
                results["name"] = " ".join(full_name_parts)

  
        job_keywords = ["مهندس", "Software Engineer", "Developer", "برمجيات", "نظم", "مدمجة", "Manager"]
        
        for token in doc:
            word = token.text.strip()
           
            if word in job_keywords or (token.pos_ == "PROPN" and any(j in word for j in job_keywords)):
                if results["job_title"] == "Not Specified":
                    results["job_title"] = word
                else:
                  
                    results["job_title"] += f" {word}"

          
            if token.pos_ in ["NOUN", "PROPN"] and word not in noise_words:
              
                if len(word) > 2 and word not in results["name"] and word not in results["job_title"]:
                   
                    if token.ent_type_ == "ORG" or word in results["organizations"]:
                        if word not in results["organizations"]: results["organizations"].append(word)
                    else:
                        results["skills"].append(word)

    
        results["skills"] = list(dict.fromkeys(results["skills"]))[:10]
        results["organizations"] = [o for o in list(dict.fromkeys(results["organizations"])) if o not in noise_words]
        
        return results