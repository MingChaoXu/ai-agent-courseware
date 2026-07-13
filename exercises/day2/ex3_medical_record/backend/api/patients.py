"""
Patient Database API - CRUD + Timeline Analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any

router = APIRouter(prefix="/patients", tags=["patients"])

# Import DB (lazy to avoid circular import issues at startup)
_db = None

def _get_db():
    global _db
    if _db is None:
        from db.database import (
            create_patient, list_patients, get_patient, update_patient, delete_patient,
            add_visit, get_visits, get_visit, delete_visit, get_patient_timeline_text
        )
        _db = {
            "create_patient": create_patient, "list_patients": list_patients,
            "get_patient": get_patient, "update_patient": update_patient,
            "delete_patient": delete_patient, "add_visit": add_visit,
            "get_visits": get_visits, "get_visit": get_visit,
            "delete_visit": delete_visit, "get_timeline_text": get_patient_timeline_text,
        }
    return _db


# ---- Request Models ----

class PatientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    gender: str = Field("未知")
    age: Optional[int] = None
    phone: str = Field("")
    id_card: str = Field("")
    notes: str = Field("")

class PatientUpdateRequest(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    id_card: Optional[str] = None
    notes: Optional[str] = None

class VisitAddRequest(BaseModel):
    patient_id: int
    module: str
    input_text: str
    result: Any

class TimelineAnalysisRequest(BaseModel):
    patient_id: int


# ---- Patient Endpoints ----

@router.get("")
async def api_list_patients(keyword: str = ""):
    """List all patients, optional keyword search."""
    db = _get_db()
    return db["list_patients"](keyword)


@router.post("")
async def api_create_patient(req: PatientCreateRequest):
    """Create a new patient."""
    db = _get_db()
    return db["create_patient"](
        name=req.name, gender=req.gender, age=req.age,
        phone=req.phone, id_card=req.id_card, notes=req.notes
    )


@router.get("/{patient_id}")
async def api_get_patient(patient_id: int):
    """Get patient details."""
    db = _get_db()
    patient = db["get_patient"](patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}")
async def api_update_patient(patient_id: int, req: PatientUpdateRequest):
    """Update patient info."""
    db = _get_db()
    patient = db["get_patient"](patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    return db["update_patient"](patient_id, **updates)


@router.delete("/{patient_id}")
async def api_delete_patient(patient_id: int):
    """Delete a patient and all their visits."""
    db = _get_db()
    ok = db["delete_patient"](patient_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"status": "deleted"}


# ---- Visit Endpoints ----

@router.get("/{patient_id}/visits")
async def api_get_visits(patient_id: int):
    """Get all visits for a patient."""
    db = _get_db()
    patient = db["get_patient"](patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db["get_visits"](patient_id)


@router.post("/visits")
async def api_add_visit(req: VisitAddRequest):
    """Add a visit record."""
    db = _get_db()
    patient = db["get_patient"](req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db["add_visit"](req.patient_id, req.module, req.input_text, req.result)


@router.delete("/visits/{visit_id}")
async def api_delete_visit(visit_id: int):
    """Delete a visit record."""
    db = _get_db()
    ok = db["delete_visit"](visit_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Visit not found")
    return {"status": "deleted"}


# ---- Timeline Analysis ----

@router.post("/timeline-analysis")
async def api_timeline_analysis(req: TimelineAnalysisRequest):
    """Run AI timeline analysis for a patient."""
    db = _get_db()
    patient = db["get_patient"](req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    timeline_text = db["get_timeline_text"](req.patient_id)
    if not timeline_text.strip():
        raise HTTPException(status_code=400, detail="No visit records found for this patient")

    # Use the agent to analyze
    from api.chat import agent_instance
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    from agent.agent import analyze
    result = analyze(agent_instance, "timeline", timeline_text)
    return {"patient": patient, "timeline_text": timeline_text, "analysis": result}
