"""
Health check API
"""

from fastapi import APIRouter
from models.schemas import HealthResponse
from config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health, LLM config, and AMap mode."""
    from api.chat import agent_instance
    agent_ready = agent_instance is not None
    modules = ["incident_analysis", "impact_assessment", "dispatch_plan", "info_publish", "review_report"] if agent_ready else []
    return HealthResponse(
        status="ok" if settings.is_configured() else "not_configured",
        llm_configured=bool(settings.LLM_API_KEY),
        agent_ready=agent_ready,
        amap_mode=settings.amap_mode,
        modules=modules,
    )
