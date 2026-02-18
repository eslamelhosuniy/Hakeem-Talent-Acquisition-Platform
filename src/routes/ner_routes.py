from fastapi import APIRouter
from pydantic import BaseModel
from controllers.ner_controller import classify_text

router = APIRouter()


class TextRequest(BaseModel):
    text: str


@router.post("/ner")
def ner_endpoint(data: TextRequest):
    return classify_text(data.text)
