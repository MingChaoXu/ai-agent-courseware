"""Drone fleet management API."""
from fastapi import APIRouter, HTTPException
from models.schemas import DroneStatus, DroneControl
from db import database as db

router = APIRouter(prefix="/drones", tags=["drones"])


@router.get("", response_model=list[DroneStatus])
async def list_drones():
    return db.get_all_drones()


@router.get("/{drone_id}", response_model=DroneStatus)
async def get_drone(drone_id: int):
    d = db.get_drone(drone_id)
    if not d:
        raise HTTPException(status_code=404, detail="Drone not found")
    return d


@router.post("/{drone_id}/control")
async def control_drone(drone_id: int, action: DroneControl):
    d = db.get_drone(drone_id)
    if not d:
        raise HTTPException(status_code=404, detail="Drone not found")

    updates = {}
    if action.action == "takeoff":
        updates["status"] = "flying"
        updates["altitude"] = action.altitude or 100.0
    elif action.action == "land":
        updates["status"] = "idle"
        updates["altitude"] = 0.0
        updates["speed"] = 0.0
    elif action.action == "return":
        updates["status"] = "flying"
        updates["lat"] = settings_lat()
        updates["lng"] = settings_lng()
    elif action.action == "hover":
        updates["speed"] = 0.0
    elif action.action == "goto":
        if action.lat:
            updates["lat"] = action.lat
        if action.lng:
            updates["lng"] = action.lng
        if action.altitude:
            updates["altitude"] = action.altitude

    if updates:
        db.update_drone(drone_id, **updates)
    return {"status": "ok", "drone_id": drone_id, "updates": updates}


def settings_lat():
    from config import settings
    return settings.CITY_CENTER_LAT


def settings_lng():
    from config import settings
    return settings.CITY_CENTER_LNG
