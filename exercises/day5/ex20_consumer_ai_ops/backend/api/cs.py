"""Customer service endpoints - RAG + Multi-Agent pipeline."""

from fastapi import APIRouter, HTTPException

from models.schemas import CSChatRequest
from data_loader import DataLoader
from services.cs_engine import cs_chat as _cs_chat
from services.cs_engine import get_faq_suggestions, get_conversation_history

router = APIRouter()


@router.post("/cs/chat")
def cs_chat(req: CSChatRequest):
    """Chat with AI customer service."""
    result = _cs_chat(req.question, req.session_id)
    if "error" in result and result.get("error", "").startswith("LLM"):
        raise HTTPException(503, result["error"])
    return result


@router.get("/cs/faq")
def cs_faq(category: str = None):
    """Get FAQ list, optionally filtered by category."""
    return {"items": get_faq_suggestions(category)}


@router.get("/cs/stats")
def cs_stats():
    """Get CS statistics."""
    return DataLoader.cs_stats()


@router.get("/cs/history/{session_id}")
def cs_history(session_id: str):
    """Get conversation history."""
    return {"messages": get_conversation_history(session_id)}
