from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from controllers.NERController import NERController

router = APIRouter(prefix="/ner", tags=["NER"])

class TextInput(BaseModel):
    text: str

@router.post("/extract")
async def extract_entities(data: TextInput):
    controller = NERController()
    is_success, signal, result = controller.extract_entities(data.text)
    if is_success:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"signal": signal, "data": result}
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"signal": signal, "error": result}
    )