# Hakeem-Talent-Acquisition-Platform
An end-to-end AI-powered talent platform that empowers companies to hire smarter and helps candidates get matched to the right opportunities through intelligent resume analysis and natural language search.

## Structure

```
src/
├── main.py
├── controllers/
├── helpers/
├── models/
├── routes/
└── stores/
    ├── llm/
    └── vectordb/
```

## Usage

```bash
cp .env.example .env
# Then update the .env file with required environment variables
pip install -r requirements.txt
uvicorn main:app --reload
```




# 🧠 AI Talent Acquisition Platform

An AI-powered backend system for smart hiring and candidate evaluation.
The platform extracts structured information from CVs, performs Named Entity Recognition (NER), and prepares data for intelligent candidate-job matching.

---

## 🚀 Features

* 📄 **CV Parsing**

  * Extracts text and structured data from resumes (PDF/DOCX)

* 🧠 **Named Entity Recognition (NER)**

  * Uses spaCy to extract entities such as:

    * Names
    * Organizations
    * Locations

* ⚙️ **RESTful API (FastAPI)**

  * Fully documented APIs using Swagger UI

* 🧪 **Testing Ready**

  * Easily test endpoints via Swagger or Postman

---

## 🛠️ Tech Stack

* **Backend:** FastAPI
* **NLP:** spaCy
* **Database:** PostgreSQL (via SQLAlchemy)
* **Vector DB:** Qdrant
* **AI Integration:** OpenAI API (optional)

---

## 📦 Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/eslamelhosuniy/Hakeem-Talent-Acquisition-Platform.git
cd Hakeem-Talent-Acquisition-Platform
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Install spaCy Model (Important ⚠️)

```bash
python -m spacy download xx_ent_wiki_sm
```

---

### 5️⃣ Run the Server

```bash
cd src
python -m uvicorn main:app --reload
```

---

## 🌐 API Endpoints

### 🔹 Base

* `GET /` → Health check
* `GET /api/v1/` → Welcome message

---

### 🔹 CV Parser

* `POST /cv/parse` → Parse CV text
* `POST /cv/parse-file` → Upload and parse CV file

---

### 🔹 NER

* `POST /ner/extract` → Extract entities from text

---

### 🔹 Debug

* `POST /debug/skills-test` → Test skill matching logic

---

## 📬 API Documentation

After running the server, open:

```bash
http://127.0.0.1:8000/docs
```

---

## 🧪 Example Requests

### CV Parsing (Postman)

* Method: `POST`
* URL: `http://127.0.0.1:8000/cv/parse-file`
* Body → form-data:

  * key: `file`
  * type: File
  * value: upload your CV

---

### NER Extraction

```json
{
  "text": "Ahmed Ali worked at Google in Cairo as a Python developer."
}
```

---

## ⚠️ Notes

* Make sure spaCy model is installed before running the server
* Some features (like OpenAI or database) may require environment variables

---

## 📌 Future Improvements

* 🔍 Semantic matching using embeddings
* 📊 Candidate ranking system
* 🧠 Explainable AI for hiring decisions

---

## 👨‍💻 Author

Developed as part of an AI-powered recruitment system project.







