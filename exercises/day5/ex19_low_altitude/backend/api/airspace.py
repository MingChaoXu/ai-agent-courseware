"""Airspace management API: events, flight paths, dashboard."""
from fastapi import APIRouter, HTTPException
from models.schemas import EventInfo, DashboardData, FlightPath
from db import database as db
from cv_service.yolo_server import get_cv_service

router = APIRouter(tags=["airspace"])


@router.get("/events", response_model=list[EventInfo])
async def list_events():
    return db.get_all_events()


@router.get("/events/active", response_model=list[EventInfo])
async def active_events():
    return db.get_active_events()


@router.post("/events/{event_id}/resolve")
async def resolve_event(event_id: int):
    db.update_event(event_id, status="resolved")
    return {"status": "ok", "event_id": event_id}


@router.get("/flight-paths", response_model=list[FlightPath])
async def list_flight_paths():
    return db.get_all_flight_paths()


@router.get("/dashboard", response_model=DashboardData)
async def dashboard():
    from config import settings
    drones = db.get_all_drones()
    orders = db.get_all_orders()
    events = db.get_all_events()
    paths = db.get_all_flight_paths()
    cv_service = get_cv_service()

    active_drones = sum(1 for d in drones if d["status"] == "flying")
    pending_orders = sum(1 for o in orders if o["status"] in ("pending", "assigned"))
    active_events = sum(1 for e in events if e["status"] in ("active", "monitoring"))

    return DashboardData(
        drones=drones,
        orders=orders,
        events=events,
        flight_paths=paths,
        cv_model_status={
            "loaded": cv_service.is_loaded,
            "model": settings.YOLO_MODEL,
            "device": settings.YOLO_DEVICE,
            "samples": cv_service.list_samples(),
        },
        stats={
            "total_drones": len(drones),
            "flying_drones": active_drones,
            "idle_drones": sum(1 for d in drones if d["status"] == "idle"),
            "pending_orders": pending_orders,
            "active_events": active_events,
            "avg_battery": round(sum(d["battery"] for d in drones) / max(len(drones), 1), 1),
        },
    )
