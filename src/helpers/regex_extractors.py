import re
from datetime import datetime


# Extract email 
def extract_email(text):
    emails = re.findall(
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        text,
        re.IGNORECASE
    )
    return emails[0] if emails else None


# Extract phone 
def extract_phone(text):
    patterns = [
        r"\+?\d{1,4}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}",  # عام
        r"\d{4}[\s.-]?\d{3}[\s.-]?\d{4}", 
        r"\+20[\s.-]?1[0-2,5]\d{8}",  
        r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", 
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = re.sub(r'\s+', ' ', match.group(0).strip())
        
            digits_only = re.sub(r'\D', '', phone)
            if len(digits_only) >= 10:
                return phone
    
    return None


# Extract gender 
def extract_gender(text):
    text = text.lower()
    
    male_patterns = [
        r"\b(male|man|gender\s*:\s*m\b|sex\s*:\s*m\b|mr\.|mr\b)",
    ]
    
    female_patterns = [
        r"\b(female|woman|gender\s*:\s*f\b|sex\s*:\s*f\b|mrs\.|ms\.|miss\b)",
    ]
    
    for pattern in male_patterns:
        if re.search(pattern, text):

            return "male"
    
    for pattern in female_patterns:
        if re.search(pattern, text):
            return "female"
    
    return None


# Extract degree 
def extract_degree(text):
    text_lower = text.lower()
    
    degree_patterns = [
        # Bachelor's
        r"bachelor'?s?\s*(?:of\s*)?(?:science|arts)?\s*(?:in\s*)?(?:computer science|cs|software engineering|information technology|it|computer engineering)",
        r"b\.?s\.?c?\.?\s*(?:in\s*)?(?:computer science|cs|software engineering|information technology|it)",
        r"bsc\s*(?:in\s*)?(?:computer science|cs|software engineering|it)",
        r"bs\s+(?:computer science|cs|software engineering|it)",
        
        # Master's
        r"master'?s?\s*(?:of\s*)?(?:science|arts)?\s*(?:in\s*)?(?:computer science|cs|software engineering|information technology|it|data science|ai|artificial intelligence)",
        r"m\.?s\.?c?\.?\s*(?:in\s*)?(?:computer science|cs|software engineering|it|data science)",
        r"msc\s*(?:in\s*)?(?:computer science|cs|it)",
        
        # PhD
        r"ph\.?d\.?\s*(?:in\s*)?(?:computer science|cs|software engineering|it)",
        r"doctorate\s*(?:in\s*)?(?:computer science|cs)",
        
        # Diploma
        r"diploma\s*(?:in\s*)?(?:computer science|cs|software engineering|it)",
        r"associate\s*degree\s*(?:in\s*)?(?:computer science|cs|it)",
    ]
    
    for pattern in degree_patterns:
        match = re.search(pattern, text_lower)
        if match:
            
            start, end = match.span()
            return text[start:end].strip()
    
    return None


# Extract years 
def extract_years(text: str):
    text_lower = text.lower()
    
    
    experience_sections = [
        r"(?:work\s+)?experience[:\s]+(.*?)(?=education|skills|projects|certifications|languages|additional|$)",
        r"employment\s+history[:\s]+(.*?)(?=education|skills|$)",
        r"professional\s+(?:experience|summary)[:\s]+(.*?)(?=education|skills|$)",
    ]
    
    source_text = text_lower
    for pattern in experience_sections:
        section = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
        if section:
            source_text = section.group(1)
            break
    

    year_pattern = r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)?\s*(19\d{2}|20\d{2})\b"
    
    years = re.findall(year_pattern, source_text, re.IGNORECASE)
    

    current_pattern = r"\b(current|present|now|till\s+date|ongoing|today)\b"
    has_current = bool(re.search(current_pattern, source_text, re.IGNORECASE))
    

    numeric_years = [int(y) for y in years if y.strip()]
    
    if not numeric_years:
        return None
    
    start_year = min(numeric_years)
    end_year = datetime.now().year if has_current else max(numeric_years)
    
    return {
        "from": start_year,
        "to": end_year,
        "experience_years": max(0, end_year - start_year)
    }


COMMON_SKILLS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c",
    "php", "ruby", "swift", "kotlin", "go", "golang", "rust", "scala",
    "r", "matlab", "perl",
    
    # Web Technologies
    "html", "html5", "css", "css3", "sass", "scss", "less",
    "xml", "json",
    
    # Frameworks & Libraries
    "react", "reactjs", "angular", "vue", "vuejs", "svelte",
    "django", "flask", "fastapi", "spring", "springboot",
    "node", "nodejs", "express", "expressjs", "nestjs",
    "jquery", "bootstrap", "tailwind", "tailwindcss",
    "laravel", "symfony", "rails",
    
    # Databases
    "sql", "mysql", "postgresql", "postgres", "sqlite",
    "mongodb", "redis", "oracle", "mssql", "cassandra", "dynamodb",
    
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud",
    "docker", "kubernetes", "k8s", "jenkins", "ci/cd",
    "terraform", "ansible", "vagrant",
    
    # Tools & Others
    "git", "github", "gitlab", "bitbucket",
    "linux", "unix", "windows", "macos",
    "rest", "restful", "api", "rest api", "rest apis",  # أضفنا النسخ المركبة
    "graphql", "grpc",
    "unit testing", "integration testing",  # أضفنا النسخ الكاملة
    "jest", "pytest", "junit", "selenium", "cypress",
    "webpack", "vite", "babel",
    "nginx", "apache",
    "agile", "scrum", "jira",
    "machine learning", "ml", "deep learning", "ai",
    "data science", "pandas", "numpy", "tensorflow", "pytorch",
}

def extract_skills(text: str):
    text_lower = text.lower()
    
   
    skill_sections = [
        r"(?:technical\s+)?skills\s*:?\s*(.*?)(?=\n\s*[A-Z][A-Z\s]+:|education|experience|projects|certifications|$)",
        r"competencies\s*:?\s*(.*?)(?=\n\s*[A-Z][A-Z\s]+:|education|experience|$)",
        r"technologies\s*:?\s*(.*?)(?=\n\s*[A-Z][A-Z\s]+:|education|experience|$)",
    ]
    
    source_text = text_lower
    for pattern in skill_sections:
        section = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
        if section:
            source_text = section.group(1)
            break
    

    if not source_text or source_text == text_lower:
        source_text = text_lower
    
 
    source_text = re.sub(r"[•●▪→◦∙⚫]", " ", source_text)
    
  
    source_text = re.sub(r"[()[\]{}.]", ",", source_text)
    
    tokens = re.split(r"[,;\n/|&:]", source_text)
    
    skills = set()
    
    for token in tokens:
        token = token.strip()
        token = re.sub(r"\s+", " ", token)  
        
    
        token = re.sub(r"\s+\d+\.?\d*$", "", token)
        
     
        stop_words = ['and', 'or', 'the', 'a', 'an', 'in', 'of', 'to', 'for']
        if token in stop_words:
            continue
        
     
        skip_headers = ['programming languages', 'web technologies', 'frameworks', 
                       'libraries', 'databases', 'tools', 'platforms', 'testing']
        if token in skip_headers:
            continue
        

        if token in COMMON_SKILLS:
            skills.add(token)
     
        else:
            for skill in COMMON_SKILLS:
           
                if re.search(r"\b" + re.escape(skill) + r"\b", token):
                    skills.add(skill)
    
    return sorted(skills)




