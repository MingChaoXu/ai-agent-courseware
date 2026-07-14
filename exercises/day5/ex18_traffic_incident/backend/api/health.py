"""
Health check API + Geocode proxy
"""

from fastapi import APIRouter, Query
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
        amap_api_key=settings.AMAP_API_KEY,
        modules=modules,
    )


@router.get("/geocode")
async def geocode(address: str = Query(..., min_length=1, description="地址文本")):
    """Geocode proxy: 地址 → 经纬度.
    
    Uses AMapClient with online/offline fallback.
    The JS API key may not work for REST API calls (USERKEY_PLAT_NOMATCH),
    so we fall back to offline mock data when the online call fails.
    """
    from services.amap_client import AMapClient
    client = AMapClient()
    result = client.geocode(address)
    if "error" in result:
        # Force offline mode (empty key → uses mock data)
        import services.amap_client as amap_mod
        result = amap_mod.AMapClient(api_key="__offline__")._mock_geocode(address)
    return result
