from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Request
from typing import List, Optional
try:
    from controllers.data_controller import DataController
except ImportError:
    from src.controllers.data_controller import DataController

router = APIRouter(
    prefix="/cvs",
    tags=["CV Management"]
)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_cv(
    request: Request,
    job_title: str = Form(...,),
    file: UploadFile = File(..., )
):
   
    try:
    
        return await DataController.create_cv(request=request, job_title=job_title, file=file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء الرفع: {str(e)}")


@router.get("/", response_model=List[dict])
def get_all_cvs():
   
    return DataController.get_all()


@router.get("/{cv_id}")
def get_cv_by_id(cv_id: int):
   
    return DataController.get_one(cv_id)

@router.put("/{cv_id}")
async def update_cv(
    request: Request,
    cv_id: int,
    job_title: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
   
    try:
       
        return await DataController.update_cv(request=request, id=cv_id, job_title=job_title, file=file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ أثناء التحديث: {str(e)}")


@router.delete("/{cv_id}")
def delete_cv(cv_id: int):
  
    return DataController.delete(cv_id)