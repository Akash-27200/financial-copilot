"""Insights route — financial analytics."""

from fastapi import APIRouter, HTTPException
from app.routes.upload import get_transactions
from app.insights import compute_insights
from app.logger import logger

router = APIRouter()


@router.get("/insights")
async def get_insights():
    """Get computed financial insights."""
    transactions = get_transactions()
    logger.info(f"Insights requested for {len(transactions)} transactions")

    if not transactions:
        logger.warning("Insights requested with no transactions loaded")
        raise HTTPException(
            status_code=400,
            detail="No transactions loaded. Please upload a bank statement PDF first."
        )

    try:
        insights = compute_insights(transactions)
        return insights
    except Exception as e:
        logger.error(f"Insights computation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compute insights: {str(e)}")
