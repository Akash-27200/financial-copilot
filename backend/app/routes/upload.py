"""PDF upload route."""

import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.pdf_parser import extract_text_from_pdf
from app.transaction_processor import process_transactions
from app.rag_engine import rag_engine
from app.insights import compute_insights
from app.logger import logger
from app.models import UploadResponse

router = APIRouter()

# In-memory store for current session
_current_transactions = []


def get_transactions():
    return _current_transactions


@router.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a bank statement PDF and extract transactions."""
    global _current_transactions
    start_time = time.time()

    logger.info(f"File upload received: {file.filename} (content_type={file.content_type})")

    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        # Read file
        file_bytes = await file.read()
        logger.info(f"File read: {len(file_bytes)} bytes")

        # Validate size
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_bytes) > max_size:
            logger.warning(f"File too large: {len(file_bytes)} bytes")
            raise HTTPException(status_code=400, detail="File size must be under 10MB")

        # Extract text
        raw_text = extract_text_from_pdf(file_bytes, file.filename)

        # Process transactions
        transactions = process_transactions(raw_text)
        _current_transactions = transactions

        # Load into RAG engine
        rag_engine.load_transactions(transactions)

        # Calculate totals
        total_income = sum(t.amount for t in transactions if t.type == "credit")
        total_expenses = sum(t.amount for t in transactions if t.type == "debit")

        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Upload pipeline completed in {elapsed}ms — {len(transactions)} transactions extracted")

        return UploadResponse(
            message="PDF processed successfully",
            total_transactions=len(transactions),
            total_income=round(total_income, 2),
            total_expenses=round(total_expenses, 2),
            file_name=file.filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
