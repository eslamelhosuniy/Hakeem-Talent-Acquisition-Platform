from fastapi import APIRouter, UploadFile, File, Form
from controllers.data_controller import DataController

router = APIRouter(
    prefix="/data",
    tags=["CV Data"]
)


# ----------------------------
# Create CV
# ----------------------------
@router.post("/create")
async def create_cv(
        job_title: str = Form(...),
        cv: UploadFile = File(...)
):
    """
    Create a new CV with job_title and file
    """
    return await DataController.create_cv(job_title, cv)


# ----------------------------
# Get all CVs
# ----------------------------
@router.get("/")
def get_all():
    """
    Return all CV records
    """
    return DataController.get_all()


# ----------------------------
# Get single CV by ID
# ----------------------------
@router.get("/{id}")
def get_one(id: int):
    """
    Return single CV record by ID
    """
    return DataController.get_one(id)


# ----------------------------
# Update CV
# ----------------------------
@router.put("/update/{id}")
async def update_cv(
        id: int,
        job_title: str = Form(None),
        cv: UploadFile = File(None)
):
    """
    Update a CV:
    - job_title: optional new job title
    - cv: optional new file
    """
    return await DataController.update_cv(id, job_title, cv)


# ----------------------------
# Delete CV
# ----------------------------
@router.delete("/{id}")
def delete(id: int):
    """
    Delete CV by ID (also deletes the file)
    """
    return DataController.delete(id)