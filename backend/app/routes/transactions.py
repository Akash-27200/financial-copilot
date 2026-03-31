"""Transaction routes — list and CSV export."""

import csv
import io
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.routes.upload import get_transactions
from app.logger import logger

router = APIRouter()


@router.get("/transactions")
async def list_transactions(
    category: str = Query(None, description="Filter by category"),
    type: str = Query(None, description="Filter by type (debit/credit)"),
    format: str = Query("json", description="Response format: json or csv"),
):
    """Return stored transactions with optional filters."""
    transactions = get_transactions()
    logger.info(f"Transactions requested: {len(transactions)} total, filters: category={category}, type={type}, format={format}")

    # Apply filters
    filtered = transactions
    if category:
        filtered = [t for t in filtered if t.category.lower() == category.lower()]
    if type:
        filtered = [t for t in filtered if t.type.lower() == type.lower()]

    logger.info(f"Returning {len(filtered)} transactions after filtering")

    # CSV export
    if format.lower() == "csv":
        return _generate_csv(filtered)

    return {
        "transactions": [t.model_dump() for t in filtered],
        "total_count": len(filtered),
        "total_income": round(sum(t.amount for t in filtered if t.type == "credit"), 2),
        "total_expenses": round(sum(t.amount for t in filtered if t.type == "debit"), 2),
    }


def _generate_csv(transactions) -> StreamingResponse:
    """Generate CSV file from transactions."""
    logger.info(f"Generating CSV export for {len(transactions)} transactions")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Amount", "Type", "Category"])
    for t in transactions:
        writer.writerow([t.date, t.description, t.amount, t.type, t.category])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )
