import os
import io
import base64
import logging
import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from .BaseController import BaseController

# تحميل البيئة لضمان قراءة المفاتيح
load_dotenv()

logger = logging.getLogger(__name__)


class TextExtractionController(BaseController):
    """
    Text extraction controller with fallback strategy:
    1. PyMuPDFLoader - for text-based PDFs
    2. pytesseract OCR - for scanned PDFs
    3. gpt-4o/gpt-4o-mini VLM - for complex/failed cases
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

        # Step 3: Try VLM (OpenAI)
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
            import pytesseract
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
                    system_prompt = self.template_parser.get("text_extraction", "system_prompt")
                except:
                    pass

            # سحب الموديل من الـ .env
            model_id = os.getenv("GENERATION_MODEL_ID", "gpt-4o-mini")
            client = self.generation_client.client
            pages_text = []

            for page in pages:
                buffer = io.BytesIO()
                page.save(buffer, format="JPEG")
                encoded_string = base64.b64encode(buffer.getvalue()).decode("utf-8")

                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}
                                },
                                {
                                    "type": "text",
                                    "text": "استخرج كل النص الموجود في هذه الصورة باللغة العربية والإنجليزية بدقة."
                                },
                            ],
                        },
                    ],
                )

                if response and response.choices:
                    page_text = response.choices[0].message.content
                    pages_text.append(page_text)
                else:
                    pages_text.append("")

            return pages_text

        except Exception as e:
            logger.error(f"VLM extraction failed for PDF: {e}")
            return []

    def extract_image(self, file_path: str):
        """Extract text from an image file using VLM and return as OCRDocumentLoader."""
        try:
            logger.info(f"Extracting text from image: {file_path}")
            text = self.extract_text(file_path, self.generation_client, self.template_parser)
            
            if text and len(text.strip()) > 5:
                return OCRDocumentLoader(file_path, [text], extraction_method="vlm_image")
            
            # Fallback to Tesseract
            import pytesseract
            logger.warning(f"VLM returned no text for image, trying OCR: {file_path}")
            img = Image.open(file_path)
            cleaned_img = self._clean_image_for_ocr(img)
            text = pytesseract.image_to_string(cleaned_img, lang="ara+eng", config="--oem 3 --psm 6")
            
            return OCRDocumentLoader(file_path, [text] if text else [""], extraction_method="ocr_image")
            
        except Exception as e:
            logger.error(f"Error in extract_image: {e}")
            return OCRDocumentLoader(file_path, [""], extraction_method="failed_image")

    @classmethod
    def extract_text(cls, file_path: str, generation_client=None, template_parser=None) -> str:
        """Extract text from an image file using VLM (Class method used by endpoints)."""
        instance = cls(generation_client=generation_client, template_parser=template_parser) 
        
        # قراءة الموديل والـ Key مباشرة من الـ ENV لضمان أحدث قيمة
        model_id = os.getenv("GENERATION_MODEL_ID", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY")

        try:
            # 1. التحقق من وجود الـ client والـ API Key
            if not instance.generation_client or not api_key or "your_actual" in api_key:
                logger.error("[VLM] API Key missing or invalid, falling back to local extraction")
                doc = fitz.open(file_path)
                return " ".join([page.get_text() for page in doc])

            # 2. Read and encode image
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

            # 3. System Prompt
            system_prompt = "أنت مساعد متخصص في استخراج النص من الصور."
            if instance.template_parser:
                try:
                    system_prompt = instance.template_parser.get("text_extraction", "system_prompt")
                except:
                    pass

            # 4. Call VLM
            client = instance.generation_client.client
            logger.info(f"Calling VLM ({model_id}) for file: {file_path}")
            
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}},
                            {"type": "text", "text": "استخرج كل النص الموجود في هذه الصورة بدقة عالية."},
                        ],
                    },
                ],
            )

            extracted_text = response.choices[0].message.content if response else None
            return extracted_text

        except Exception as e:
            # معالجة ذكية للخطأ 401 (الرصيد أو المفتاح)
            if "401" in str(e):
                logger.error(f"VLM Auth Error (401): Check your OpenAI Balance/Key. Falling back to local.")
            else:
                logger.error(f"VLM Error: {e}. Falling back to local.")
                
            try:
                # Fallback to PyMuPDF (Fitz)
                doc = fitz.open(file_path)
                text = " ".join([page.get_text() for page in doc])
                return text if text.strip() else "Extraction failed. Please check file quality."
            except:
                return None


class OCRDocumentLoader:
    def __init__(self, file_path: str, pages_text: list, extraction_method: str = "ocr"):
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