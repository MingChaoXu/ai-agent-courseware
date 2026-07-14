"""Health check API."""
from fastapi import APIRouter
from models.schemas import HealthResponse
from config import settings
from db import database as db
from cv_service.yolo_server import get_cv_service

router = APIRouter(tags=["health"])

agent_instance = None


@router.get("/health", response_model=HealthResponse)
async def health():
    cv_service = get_cv_service()
    drones = db.get_all_drones()
    orders = db.get_pending_orders()
    events = db.get_active_events()

    return HealthResponse(
        status="ok",
        llm_configured=settings.is_configured(),
        agent_ready=agent_instance is not None,
        cv_model_loaded=cv_service.is_loaded,
        drones_count=len(drones),
        active_orders=len(orders),
        active_events=len(events),
        agents=["perception", "logistics", "traffic", "emergency"],
        amap_mode=settings.amap_mode,
        amap_api_key=settings.AMAP_API_KEY,
    )
