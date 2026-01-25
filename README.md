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
