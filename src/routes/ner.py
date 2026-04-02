from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from controllers.NERController import NERController 

router = APIRouter(prefix="/ner", tags=["NER"])


controller = NERController()

class TextInput(BaseModel):
    text: str

@router.post("/extract")
async def extract_entities(data: TextInput):
    try:
        
        is_success, signal, result = controller.extract_entities(data.text)
        
        if is_success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "signal": signal,
                    "data": result
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "signal": signal, 
                "detail": result
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "detail": str(e)}
        )