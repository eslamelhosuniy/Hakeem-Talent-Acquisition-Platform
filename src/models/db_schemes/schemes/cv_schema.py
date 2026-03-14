from pydantic import BaseModel


class CVBase(BaseModel):
    job_title: str


class CVResponse(CVBase):
    id: int
    cv_file: str

    class Config:
        from_attributes = True