from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from controllers.NERController import NERController
from controllers.data_controller import DataController 

router = APIRouter(prefix="/cv", tags=["CV Parser"])


ner_worker = NERController()

class CVRequest(BaseModel):
    text: str
    job_title: str = "General" 

@router.post("/parse")
async def parse_cv_endpoint(payload: CVRequest): 
    try:
        
        is_success, signal, result = ner_worker.extract_entities(payload.text)
        
        if is_success:
           
            db_record = await DataController.create_cv(
                file=None, 
                job_title=payload.job_title,
                ner_results=result 
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "CV parsed and saved to database",
                    "signal": signal, 
                    "data": result,
                    "db_id": db_record.id 
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "signal": signal, 
                "error": result
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "detail": str(e)}
        )