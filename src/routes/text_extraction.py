from fastapi import APIRouter, UploadFile, File, HTTPException, Request, status
from fastapi.responses import JSONResponse
from models.enums.ResponseEnums import ResponseSignal
import shutil
import os
import uuid
from controllers.TextExtractionController import TextExtractionController

router = APIRouter(
    prefix="/text-generation",
    tags=["Text Generation"],
)

@router.post("/extract")
async def extract_text_from_image(request: Request, file: UploadFile = File(...)):
    # 1. Create a temporary file
    temp_filename = f"temp_{uuid.uuid4()}_{file.filename}"
    temp_file_path = os.path.join("tmp", temp_filename)
    os.makedirs("tmp", exist_ok=True)

    try:
        # 2. Save uploaded file to disk
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Call Controller Method Directly (Class Method)
        # بنسحب الـ client والـ parser من الـ request.app اللي اتعرفوا في الـ main.py
        extracted_text = TextExtractionController.extract_text(
            file_path=temp_file_path,
            generation_client=request.app.generation_client,
            template_parser=request.app.template_parser
        )

        # ============================================================
        # سطر الـ Debug اللي ضفناه عشان نشوف النص الخام (Raw Text) قبل ما يتحول لـ JSON
        print("\n" + "!" * 30 + " VLM DEBUG START " + "!" * 30)
        print(f"EXTRACTED TEXT:\n{extracted_text}")
        print("!" * 30 + " VLM DEBUG END " + "!" * 30 + "\n")
        # ============================================================

        if extracted_text is None:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "signal": ResponseSignal.ERROR.value, 
                    "error": "Failed to extract text from image or VLM returned empty"
                }
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.SUCCESS.value, 
                "data": {"extracted_text": extracted_text}
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": ResponseSignal.ERROR.value, "error": str(e)}
        )

    finally:
        # 4. Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)