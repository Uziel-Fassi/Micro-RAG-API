import io
import logging

from fastapi import HTTPException
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes, filename: str) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:
        logger.exception("Failed to parse PDF %s", filename)
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file") from exc

    if not reader.pages:
        raise HTTPException(status_code=400, detail="Uploaded PDF has no pages")

    extracted_pages: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            extracted_pages.append(page_text)

    text = "\n".join(extracted_pages).strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found. The PDF may contain scanned images only",
        )

    return text
