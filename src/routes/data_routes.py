import fitz  # PyMuPDF
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from controllers.data_controller import DataController
from controllers.NERController import NERController


from models.db_schemes.schemes.cv_schema import CVResponse
router = APIRouter(
    prefix="/data",
    tags=["CV Data"]
)

ner_worker = NERController()

@router.post("/create", response_model=CVResponse)
async def create_cv(
    job_title: str = Form(...),
    cv: UploadFile = File(...)
):
    try:
        # 1. التحقق من نوع الملف
        if cv.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
       
        pdf_content = await cv.read()
        text = ""
        try:
            with fitz.open(stream=pdf_content, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not read PDF content: {str(e)}")
        
      
        await cv.seek(0)

      
        is_success, signal, ner_results = ner_worker.extract_entities(text)

        return await DataController.create_cv(
            file=cv, 
            job_title=job_title, 
            ner_results=ner_results if is_success else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CVResponse])
def get_all():
  
    return DataController.get_all()


@router.get("/{id}", response_model=CVResponse)
def get_one(id: int):
  
    result = DataController.get_one(id)
    if not result:
        raise HTTPException(status_code=404, detail=f"CV with ID {id} not found")
    return result


@router.get("/search/{query}", response_model=List[CVResponse])
def search(query: str):
   
    return DataController.search_cvs(query)


@router.delete("/{id}")
def delete(id: int):
   
    result = DataController.delete(id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result