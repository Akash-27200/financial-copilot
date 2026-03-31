"""PDF text extraction using pdfplumber."""

import time
import pdfplumber
from io import BytesIO
from app.logger import logger


def extract_text_from_pdf(file_bytes: bytes, filename: str) -> str:
    """Extract all text from a PDF file."""
    logger.info(f"PDF file received: {filename} ({len(file_bytes)} bytes)")
    logger.info("PDF parsing started")
    start_time = time.time()

    full_text = ""
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            logger.info(f"PDF has {page_count} page(s)")

            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                full_text += page_text + "\n"
                logger.info(f"  Page {i + 1}/{page_count}: extracted {len(page_text)} chars")

    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        raise ValueError(f"Failed to parse PDF: {e}")

    elapsed = round((time.time() - start_time) * 1000, 2)
    logger.info(f"PDF parsing completed in {elapsed}ms — total {len(full_text)} chars extracted")
    return full_text
