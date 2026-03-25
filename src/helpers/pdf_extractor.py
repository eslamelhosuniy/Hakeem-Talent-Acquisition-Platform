from typing import Optional

import fitz  # PyMuPDF


def extract_text_from_pdf_bytes(data: bytes) -> str:
    """
    Extract text from a PDF byte stream using PyMuPDF.
    """
    if not data:
        return ""

    text_parts = []

    with fitz.open(stream=data, filetype="pdf") as doc:  # type: ignore[arg-type]
        for page in doc:
            text_parts.append(page.get_text())

    return "\n".join(text_parts)


def extract_text_from_pdf_file(path: str) -> str:
    """
    Convenience helper for reading from a file path (for local debugging/scripts).
    """
    with open(path, "rb") as f:
        data = f.read()

    return extract_text_from_pdf_bytes(data)

