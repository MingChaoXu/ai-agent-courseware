"""
Health check API
"""

from fastapi import APIRouter
from models.schemas import HealthResponse
from config import settings

router = APIRouter(tags=["health"])


def get_health_data(kb_loaded: bool, total_chunks: int) -> dict:
    return {
        "status": "ok" if settings.is_configured() else "not_configured",
        "llm_configured": bool(settings.LLM_API_KEY),
        "embedding_configured": bool(settings.EMBEDDING_API_KEY),
        "knowledge_base_loaded": kb_loaded,
        "total_chunks": total_chunks,
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health and configuration status."""
    from api.chat import rag_chain
    kb_loaded = rag_chain is not None and rag_chain._kb.is_loaded if rag_chain else False
    total_chunks = rag_chain._kb.total_chunks if rag_chain and rag_chain._kb else 0
    return HealthResponse(**get_health_data(kb_loaded, total_chunks))
