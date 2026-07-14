"""Health & status endpoints."""

from fastapi import APIRouter
from config import check_config
from data_loader import DataLoader

router = APIRouter()


@router.get("/status")
def get_status():
    """Check LLM configuration and data loading status."""
    return {
        "llm_configured": check_config(),
        "data_loaded": bool(DataLoader.sales()),
    }
