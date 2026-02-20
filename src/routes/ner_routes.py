from fastapi import APIRouter
from pydantic import BaseModel
from controllers.ner_controller import NERController

router = APIRouter(prefix="/ner", tags=["NER"])

controller = NERController()


class TextInput(BaseModel):
    text: str


@router.post("/extract")
async def extract_entities(data: TextInput):
    return controller.extract_entities(data.text)