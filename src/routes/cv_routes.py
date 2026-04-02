from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from controllers.NERController import NERController
from controllers.data_controller import DataController 
import fitz

router = APIRouter(prefix="/cv", tags=["CV Parser"])


ner_worker = NERController()

class CVRequest(BaseModel):
    text: str
    job_title: str = "General"

@router.post("/parse")
async def parse_cv_text_endpoint(payload: CVRequest):
   
    is_success, signal, ner_results = ner_worker.extract_entities(payload.text)
    
    if not is_success:
        raise HTTPException(status_code=400, detail="Failed to parse text")

    result = await DataController.create_cv(file=None, job_title=payload.job_title, ner_results=ner_results)
    
    return {"status": "success", "message": "Text parsed and saved", "data": result}


@router.post("/parse-file")
async def parse_cv_file_endpoint(
    job_title: str = Form("General"),
    cv_file: UploadFile = File(...)
):
  
    try:
        if cv_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

      
        pdf_content = await cv_file.read()
        text = ""
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        
       
        await cv_file.seek(0)

        is_success, signal, ner_results = ner_worker.extract_entities(text)

     
        db_result = await DataController.create_cv(
            file=cv_file, 
            job_title=job_title, 
            ner_results=ner_results if is_success else None
        )

        return {
            "status": "success",
            "message": "CV File analyzed and saved successfully",
            "database_record": db_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))