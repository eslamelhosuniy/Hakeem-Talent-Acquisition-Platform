from fastapi import APIRouter, UploadFile, File, Form
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

    return DataController.get_one(id)


@router.delete("/{id}")
def delete(id: int):

    return DataController.delete(id)