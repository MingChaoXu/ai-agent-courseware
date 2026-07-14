"""BI analysis endpoints - ReAct Agent with data tools."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from models.schemas import BIChatRequest
from data_loader import DataLoader
from services.bi_engine import bi_analyze

router = APIRouter()


@router.get("/bi/dashboard")
def bi_dashboard():
    """Pre-computed BI dashboard data (no LLM needed)."""
    return DataLoader.dashboard_summary()


@router.post("/bi/chat")
def bi_chat(req: BIChatRequest):
    """Natural language BI analysis with LLM Agent."""
    result = bi_analyze(req.question)
    if "error" in result and result.get("error", "").startswith("LLM"):
        raise HTTPException(503, result["error"])
    return result


@router.get("/bi/sales")
def bi_sales_detail(
    region: Optional[str] = None,
    category: Optional[str] = None,
    channel: Optional[str] = None,
    date: Optional[str] = None,
):
    """Get raw sales data with optional filters."""
    records = DataLoader.sales()
    if region:
        records = [r for r in records if r["region"] == region]
    if category:
        records = [r for r in records if r["category"] == category]
    if channel:
        records = [r for r in records if r["channel"] == channel]
    if date:
        records = [r for r in records if r["date"] == date]
    return records[:100]
