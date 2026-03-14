from .BaseController import BaseController
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import numpy as np
import cv2
import base64
import os
import io
import logging

logger = logging.getLogger(__name__)


class TextExtractionController(BaseController):
    """
    Text extraction controller with fallback strategy:
    1. PyMuPDFLoader - for text-based PDFs
    2. pytesseract OCR - for scanned PDFs
    3. qwen3-vl-plus VLM - for complex/failed cases
    """

    def __init__(self, generation_client=None, template_parser=None):
        super().__init__()
        self.generation_client = generation_client
        self.template_parser = template_parser

    def _pdf_to_images(self, pdf_path: str, dpi: int = 300) -> list:
        """Convert PDF pages to PIL Images using PyMuPDF."""
        images = []
        try:
            doc = fitz.open(pdf_path)
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=matrix)

                # Convert pixmap to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)

            doc.close()
            logger.info(f"Converted {len(images)} pages to images using PyMuPDF")
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")

        return images

    def extract_pdf(self, pdf_path: str):

        # Step 1: Try PyMuPDFLoader
        if self._has_extractable_text(pdf_path):
            logger.info(f"PDF has extractable text, using PyMuPDFLoader: {pdf_path}")
            return PyMuPDFLoader(pdf_path)

        # Step 2: Try OCR with pytesseract
        logger.info(f"PDF has no extractable text, trying OCR: {pdf_path}")
        ocr_pages = self._extract_with_ocr(pdf_path)

        if ocr_pages and any(len(p.strip()) > 50 for p in ocr_pages):
            logger.info(f"OCR extraction successful: {pdf_path}")
            return OCRDocumentLoader(pdf_path, ocr_pages, extraction_method="ocr")

        # Step 3: Try VLM
        if self.generation_client:
            logger.info(f"OCR failed, trying VLM extraction: {pdf_path}")
            vlm_pages = self._extract_with_vlm(pdf_path)

            if vlm_pages and any(len(p.strip()) > 10 for p in vlm_pages):
                logger.info(f"VLM extraction successful: {pdf_path}")
                return OCRDocumentLoader(pdf_path, vlm_pages, extraction_method="vlm")

        # Fallback: Return empty loader
        logger.warning(f"All extraction methods failed: {pdf_path}")
        return OCRDocumentLoader(pdf_path, [""], extraction_method="failed")

    def _has_extractable_text(self, pdf_path: str) -> bool:
        """Check if PDF contains extractable text using PyMuPDF."""
        try:
            docs = PyMuPDFLoader(pdf_path).load()
            for doc in docs:
                if doc.page_content and len(doc.page_content.strip()) > 50:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking PDF text: {e}")
            return False

    def _extract_with_ocr(self, pdf_path: str) -> list:
        """Extract text using pytesseract OCR. Returns list of page texts."""
        try:
            pages = self._pdf_to_images(pdf_path, dpi=300)
            pages_text = []

            for page in pages:
                cleaned_img = self._clean_image_for_ocr(page)
                page_text = pytesseract.image_to_string(
                    cleaned_img, lang="ara+eng", config="--oem 3 --psm 6"
                )
                pages_text.append(page_text)

            return pages_text

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []

    def _clean_image_for_ocr(self, img):
        """Clean and preprocess image for better OCR results."""
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 3)
        gray = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
        )
        return gray

    def _extract_with_vlm(self, pdf_path: str) -> list:
        """Extract text using Vision Language Model for all pages. Returns list of page texts."""
        try:
            pages = self._pdf_to_images(pdf_path, dpi=200)
            if not pages:
                return []

            system_prompt = "أنت مساعد متخصص في استخراج النص من المستندات. قم باستخراج كل النص المرئي في الصورة بدقة."
            if self.template_parser:
                try:
                    system_prompt = self.template_parser.get(
                        "text_extraction", "system_prompt"
                    )
                except:
                    pass

            client = self.generation_client.client
            pages_text = []

            for page in pages:
                buffer = io.BytesIO()
                page.save(buffer, format="JPEG")
                encoded_string = base64.b64encode(buffer.getvalue()).decode("utf-8")

                response = client.chat.completions.create(
                    model="qwen3-vl-plus",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{encoded_string}"
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "استخرج كل النص الموجود في هذه الصورة.",
                                },
                            ],
                        },
                    ],
                )

                if response and response.choices and response.choices[0].message:
                    page_text = response.choices[0].message.content
                    pages_text.append(page_text)
                else:
                    pages_text.append("")

            return pages_text

        except Exception as e:
            logger.error(f"VLM extraction failed: {e}")
            return []

    def extract_image(self, file_path: str):
        """
        Extract text from an image file using VLM and return as OCRDocumentLoader.
        """
        try:
            logger.info(f"Extracting text from image: {file_path}")
            text = self.extract_text(file_path)
            
            if text:
                return OCRDocumentLoader(file_path, [text], extraction_method="vlm_image")
            
            # Fallback to Tesseract if VLM returned nothing
            logger.warning(f"VLM returned no text for image, trying OCR: {file_path}")
            img = Image.open(file_path)
            cleaned_img = self._clean_image_for_ocr(img)
            text = pytesseract.image_to_string(cleaned_img, lang="ara+eng", config="--oem 3 --psm 6")
            
            return OCRDocumentLoader(file_path, [text] if text else [""], extraction_method="ocr_image")
            
        except Exception as e:
            logger.error(f"Error in extract_image: {e}")
            return OCRDocumentLoader(file_path, [""], extraction_method="failed_image")

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from an image file using VLM.
        Used by /api/v1/text-generation/extract endpoint.
        """
        try:
            # Validation
            if self.app_settings.IMAGE_MAX_SIZE:
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if file_size_mb > self.app_settings.IMAGE_MAX_SIZE:
                    raise ValueError(
                        f"File size exceeds limit of {self.app_settings.IMAGE_MAX_SIZE} MB"
                    )

            if self.app_settings.IMAGE_ALLOWED_TYPES:
                import mimetypes

                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type and mime_type not in self.app_settings.IMAGE_ALLOWED_TYPES:
                    raise ValueError(
                        f"File type {mime_type} not allowed. Allowed: {self.app_settings.IMAGE_ALLOWED_TYPES}"
                    )

            # Read and encode image
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

            # Get system prompt
            system_prompt = "أنت مساعد متخصص في استخراج النص من الصور."
            if self.template_parser:
                try:
                    system_prompt = self.template_parser.get(
                        "text_extraction", "system_prompt"
                    )
                except:
                    pass

            # Call VLM
            if not self.generation_client or not hasattr(self.generation_client, "client"):
                logger.error("[TextExtraction] generation_client or its base client is missing")
                return None

            client = self.generation_client.client
            response = client.chat.completions.create(
                model="qwen3-vl-plus",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_string}"
                                },
                            },
                            {
                                "type": "text",
                                "text": "استخرج كل النص الموجود في هذه الصورة.",
                            },
                        ],
                    },
                ],
            )

            if response and response.choices and response.choices[0].message:
                return response.choices[0].message.content

            return None

        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            return None


class OCRDocumentLoader:
    """
    LangChain-compatible document loader for OCR/VLM-extracted text.
    Implements the same interface as PyMuPDFLoader.
    Returns list of Documents, one per page with proper metadata.
    """

    def __init__(
        self, file_path: str, pages_text: list, extraction_method: str = "ocr"
    ):
        self.file_path = file_path
        self.pages_text = pages_text
        self.extraction_method = extraction_method
        self.file_name = os.path.basename(file_path)

    def load(self):
        documents = []
        for page_num, page_content in enumerate(self.pages_text, start=1):
            documents.append(
                Document(
                    page_content=page_content,
                    metadata={
                        "source": self.file_path,
                        "file_path": self.file_path,
                        "file_name": self.file_name,
                        "page": page_num,
                        "total_pages": len(self.pages_text),
                        "extraction_method": self.extraction_method,
                    },
                )
            )
        return documents
