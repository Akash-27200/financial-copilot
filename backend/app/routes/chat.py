"""Chat route — RAG-powered financial chatbot."""

from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.rag_engine import rag_engine
from app.logger import logger

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI financial copilot."""
    logger.info(f"Chat request: '{request.message}'")

    if not rag_engine.transactions:
        logger.warning("Chat attempted with no transactions loaded")
        raise HTTPException(
            status_code=400,
            detail="No transactions loaded. Please upload a bank statement PDF first."
        )

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = rag_engine.chat(request.message)
        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI chat error: {str(e)}")
