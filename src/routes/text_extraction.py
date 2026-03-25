from fastapi import APIRouter, UploadFile, File, HTTPException, Request, status
from fastapi.responses import JSONResponse
from controllers.TextExtractionController import TextExtractionController
from models.enums.ResponseEnums import ResponseSignal
import shutil
import os
import uuid

router = APIRouter(
    prefix="/text-generation",
    tags=["Text Generation"],
)

@router.post("/extract")
async def extract_text_from_image(request: Request, file: UploadFile = File(...)):

    # Create a temporary file
    temp_filename = f"temp_{uuid.uuid4()}_{file.filename}"
    temp_file_path = os.path.join("tmp", temp_filename)

    # Ensure tmp directory exists
    os.makedirs("tmp", exist_ok=True)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Initialize controller with generation_client from app state
        text_extraction_controller = TextExtractionController()
        text_extraction_controller.generation_client = request.app.generation_client
        text_extraction_controller.template_parser = request.app.template_parser

        extracted_text = text_extraction_controller.extract_text(temp_file_path)

        if extracted_text is None:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"signal": ResponseSignal.ERROR.value, "error": "Failed to extract text from image"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"signal": ResponseSignal.SUCCESS.value, "data": {"extracted_text": extracted_text}}
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             content={"signal": ResponseSignal.ERROR.value, "error": str(e)}
        )

    finally:
        # Clean up
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
