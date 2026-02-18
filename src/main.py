from fastapi import FastAPI
from routes.ner_routes import router as ner_router

app = FastAPI(
    title="NER API",
    description="Arabic + English Named Entity Recognition",
    version="1.0"
)

app.include_router(ner_router, prefix="/api")
