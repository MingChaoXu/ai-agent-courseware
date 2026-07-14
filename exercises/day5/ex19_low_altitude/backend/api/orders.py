"""Logistics orders API."""
from fastapi import APIRouter, HTTPException
from models.schemas import OrderInfo, CreateOrder
from db import database as db

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderInfo])
async def list_orders():
    return db.get_all_orders()


@router.get("/pending", response_model=list[OrderInfo])
async def pending_orders():
    return db.get_pending_orders()


@router.post("", response_model=OrderInfo)
async def create_order(order: CreateOrder):
    return db.create_order(
        pickup_lat=order.pickup_lat, pickup_lng=order.pickup_lng,
        dropoff_lat=order.dropoff_lat, dropoff_lng=order.dropoff_lng,
        pickup_name=order.pickup_name, dropoff_name=order.dropoff_name,
        cargo_type=order.cargo_type, weight=order.weight,
        priority=order.priority, description=order.description,
    )


@router.post("/{order_id}/assign/{drone_id}")
async def assign_drone(order_id: int, drone_id: int):
    drone = db.get_drone(drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    if drone["status"] != "idle":
        raise HTTPException(status_code=400, detail=f"Drone {drone_id} is not idle")
    db.update_order(order_id, status="assigned", drone_id=drone_id)
    db.update_drone(drone_id, status="flying", order_id=order_id)
    return {"status": "ok", "order_id": order_id, "drone_id": drone_id}


@router.post("/{order_id}/deliver")
async def mark_delivered(order_id: int):
    db.update_order(order_id, status="delivered")
    return {"status": "ok", "order_id": order_id}
