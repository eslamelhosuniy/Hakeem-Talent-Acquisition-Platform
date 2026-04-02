import fitz  # PyMuPDF
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from controllers.data_controller import DataController
from controllers.NERController import NERController

router = APIRouter(
    prefix="/data",
    tags=["CV Data"]
)


ner_worker = NERController()

@router.post("/create")
async def create_cv(
    job_title: str = Form(...),
    cv: UploadFile = File(...)
):
    try:
    
        if cv.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        pdf_content = await cv.read()
        text = ""
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        
      
        await cv.seek(0)

       
        is_success, signal, ner_results = ner_worker.extract_entities(text)

        
       
        return await DataController.create_cv(
            file=cv, 
            job_title=job_title, 
            ner_results=ner_results if is_success else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get_all():

    return DataController.get_all()


@router.get("/{id}")
def get_one(id: int):

    result = DataController.get_one(id)
    if not result:
        raise HTTPException(status_code=404, detail=f"CV with ID {id} not found")
    return result


@router.get("/search/{query}")
def search(query: str):
   
    return DataController.search_cvs(query)


@router.delete("/{id}")
def delete(id: int):
    
    result = DataController.delete(id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result