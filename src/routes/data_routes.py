from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from controllers.data_controller import DataController

router = APIRouter(
    prefix="/data",
    tags=["CV Data"]
)

 
@router.post("/create")
async def create_cv(
    job_title: str = Form(...),
    cv: UploadFile = File(...)
):

    return await DataController.create_cv(job_title, cv)


@router.get("/")
def get_all():

    return DataController.get_all()


@router.get("/{id}")
def get_one(id: int):
   
    result = DataController.get_one(id)
    if not result:
        raise HTTPException(status_code=404, detail=f"CV with ID {id} not found")
    return result

@router.put("/update/{id}")
async def update_cv(
    id: int,
    job_title: str = Form(None),
    cv: UploadFile = File(None)
):

    result = await DataController.update_cv(id, job_title, cv)
    
  
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result

@router.delete("/{id}")
def delete(id: int):
  
    result = DataController.delete(id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result