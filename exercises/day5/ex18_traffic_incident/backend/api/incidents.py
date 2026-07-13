"""
Incident Database API - CRUD + Dispatch records
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from models.schemas import IncidentCreateRequest, IncidentUpdateRequest, DispatchAddRequest

router = APIRouter(prefix="/incidents", tags=["incidents"])

_db = None


def _get_db():
    global _db
    if _db is None:
        from db.database import (
            create_incident, list_incidents, get_incident, update_incident, delete_incident,
            add_dispatch, get_dispatches, get_dispatch, delete_dispatch,
        )
        _db = {
            "create_incident": create_incident, "list_incidents": list_incidents,
            "get_incident": get_incident, "update_incident": update_incident,
            "delete_incident": delete_incident, "add_dispatch": add_dispatch,
            "get_dispatches": get_dispatches, "get_dispatch": get_dispatch,
            "delete_dispatch": delete_dispatch,
        }
    return _db


# ============================================================
# Incident Endpoints
# ============================================================

@router.get("")
async def api_list_incidents(keyword: str = "", status: str = ""):
    """List all incidents, optional keyword/status filter."""
    db = _get_db()
    return db["list_incidents"](keyword, status)


@router.post("")
async def api_create_incident(req: IncidentCreateRequest):
    """Create a new incident record."""
    db = _get_db()
    return db["create_incident"](
        description=req.description, incident_type=req.incident_type,
        location=req.location, severity=req.severity, status=req.status,
    )


@router.get("/{incident_id}")
async def api_get_incident(incident_id: int):
    """Get incident details."""
    db = _get_db()
    incident = db["get_incident"](incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/{incident_id}")
async def api_update_incident(incident_id: int, req: IncidentUpdateRequest):
    """Update incident info."""
    db = _get_db()
    incident = db["get_incident"](incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    return db["update_incident"](incident_id, **updates)


@router.delete("/{incident_id}")
async def api_delete_incident(incident_id: int):
    """Delete an incident and all its dispatch records."""
    db = _get_db()
    ok = db["delete_incident"](incident_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "deleted"}


# ============================================================
# Dispatch Endpoints
# ============================================================

@router.get("/{incident_id}/dispatches")
async def api_get_dispatches(incident_id: int):
    """Get all dispatch records for an incident."""
    db = _get_db()
    incident = db["get_incident"](incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db["get_dispatches"](incident_id)


@router.post("/dispatches")
async def api_add_dispatch(req: DispatchAddRequest):
    """Add a dispatch record for an incident."""
    db = _get_db()
    incident = db["get_incident"](req.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db["add_dispatch"](
        req.incident_id, req.analysis_text, req.dispatch_plan,
        req.publish_text, req.review_report,
    )


@router.delete("/dispatches/{dispatch_id}")
async def api_delete_dispatch(dispatch_id: int):
    """Delete a dispatch record."""
    db = _get_db()
    ok = db["delete_dispatch"](dispatch_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    return {"status": "deleted"}
