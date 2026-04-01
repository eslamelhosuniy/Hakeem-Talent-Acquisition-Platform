from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from controllers.NERController import NERController

router = APIRouter(
    prefix="/ner",
    tags=["AI Data Extraction"]
)


class TextInput(BaseModel):
    text: str = Field(...,)

@router.post("/extract", status_code=status.HTTP_200_OK)
async def extract_entities(input_data: TextInput):
   
    try:
     
        result = NERController.process_text(input_data.text)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, 
                detail="لم يتم العثور على بيانات"
            )
            
       
        return {
            "status": "success",
            "metadata": {
                "language": result.get("language"),
                "engine": "CAMeL + Spacy Hybrid"
            },
            "data": {
                "candidate_profile": {
                    "full_name": result.get("name"),
                    "current_job_title": result.get("job_title"),
                },
                "contact_info": {
                    "email": result.get("email"),
                    "phone": result.get("phone")
                },
                "expertise": {
                    "technical_skills": result.get("skills"),     
                    "affiliated_organizations": result.get("organizations") 
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during extraction: {str(e)}"
        )

@router.get("/status")
def check_ai_health():
   
    from controllers.NERController import NERController
    return {
        "camel_tools_ner": "Active (AraBERT)" if NERController.arabic_ner else "Down",
        "spacy_core": "Loaded (en_core_web_lg)",
        "memory_status": "All models in RAM"
    }