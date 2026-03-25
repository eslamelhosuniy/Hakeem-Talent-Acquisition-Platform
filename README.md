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

## Skill matching quick test

- **Run Node helper script** (from repo root, with the API running on port 8000):

```bash
npm run test:skills
```

This will:
- Load `samples/sample_resume.txt`
- Call `POST /cv/parse`
- Print `extracted_skills`, top debug rows, and a short text preview.

- **Example curl for PDF resume upload**:

```bash
curl -X POST "http://localhost:8000/cv/parse-file?lang=en" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/absolute/path/to/your_resume.pdf;type=application/pdf"
```

