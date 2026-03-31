"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date as date_type


class Transaction(BaseModel):
    date: str
    description: str
    amount: float
    type: str = Field(..., description="debit or credit")
    category: str = "uncategorized"
    raw_text: Optional[str] = None


class TransactionList(BaseModel):
    transactions: list[Transaction]
    total_count: int
    total_income: float
    total_expenses: float


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    chunks_used: int
    tokens_sent: int
    response_time_ms: float


class InsightsResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    category_breakdown: dict[str, float]
    monthly_trend: list[dict]
    top_expenses: list[dict]
    unusual_spending: list[dict]


class UploadResponse(BaseModel):
    message: str
    total_transactions: int
    total_income: float
    total_expenses: float
    file_name: str
