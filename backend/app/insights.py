"""Financial insights and analytics engine."""

from collections import defaultdict
from app.models import Transaction
from app.logger import logger


def compute_insights(transactions: list[Transaction]) -> dict:
    """Compute comprehensive financial insights from transactions."""
    logger.info(f"Computing insights for {len(transactions)} transactions")

    if not transactions:
        return {
            "total_income": 0,
            "total_expenses": 0,
            "net_balance": 0,
            "category_breakdown": {},
            "monthly_trend": [],
            "top_expenses": [],
            "unusual_spending": [],
        }

    total_income = sum(t.amount for t in transactions if t.type == "credit")
    total_expenses = sum(t.amount for t in transactions if t.type == "debit")
    net_balance = total_income - total_expenses

    # Category breakdown (debits only)
    category_totals = defaultdict(float)
    for t in transactions:
        if t.type == "debit":
            category_totals[t.category] += t.amount
    category_breakdown = dict(sorted(category_totals.items(), key=lambda x: -x[1]))

    # Monthly trend
    monthly_data = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for t in transactions:
        month_key = t.date[:7] if len(t.date) >= 7 else t.date[:5]
        if t.type == "credit":
            monthly_data[month_key]["income"] += t.amount
        else:
            monthly_data[month_key]["expenses"] += t.amount

    monthly_trend = []
    for month in sorted(monthly_data.keys()):
        d = monthly_data[month]
        monthly_trend.append({
            "month": month,
            "income": round(d["income"], 2),
            "expenses": round(d["expenses"], 2),
            "net": round(d["income"] - d["expenses"], 2),
        })

    # Top expenses
    debits = sorted([t for t in transactions if t.type == "debit"], key=lambda x: -x.amount)
    top_expenses = [
        {"date": t.date, "description": t.description, "amount": t.amount, "category": t.category}
        for t in debits[:10]
    ]

    # Unusual spending detection
    unusual_spending = _detect_unusual_spending(transactions)

    logger.info(f"Insights computed: income=₹{total_income:,.2f}, expenses=₹{total_expenses:,.2f}, categories={len(category_breakdown)}")
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(net_balance, 2),
        "category_breakdown": {k: round(v, 2) for k, v in category_breakdown.items()},
        "monthly_trend": monthly_trend,
        "top_expenses": top_expenses,
        "unusual_spending": unusual_spending,
    }


def _detect_unusual_spending(transactions: list[Transaction]) -> list[dict]:
    """Detect transactions that are unusually large for their category."""
    category_amounts = defaultdict(list)
    for t in transactions:
        if t.type == "debit":
            category_amounts[t.category].append(t)

    unusual = []
    for category, txns in category_amounts.items():
        if len(txns) < 3:
            continue
        amounts = [t.amount for t in txns]
        avg = sum(amounts) / len(amounts)
        std_dev = (sum((a - avg) ** 2 for a in amounts) / len(amounts)) ** 0.5

        if std_dev == 0:
            continue

        for t in txns:
            # Flag transactions that are 2+ standard deviations above mean
            if t.amount > avg + 2 * std_dev:
                unusual.append({
                    "date": t.date,
                    "description": t.description,
                    "amount": t.amount,
                    "category": category,
                    "avg_for_category": round(avg, 2),
                    "deviation": round((t.amount - avg) / std_dev, 2),
                })

    return sorted(unusual, key=lambda x: -x["deviation"])[:10]
