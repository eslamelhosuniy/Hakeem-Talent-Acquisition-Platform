from pydantic import BaseModel
from typing import Optional

class CVBase(BaseModel):
    job_title: str

class CVResponse(CVBase):
    id: int
    cv_file: Optional[str]
    candidate_name: Optional[str] # ضيف ده عشان يظهر في الرد
    email: Optional[str]          # ضيف ده
    phone: Optional[str]          # ضيف ده
    skills: Optional[str]         # ضيف ده

    class Config:
        from_attributes = True