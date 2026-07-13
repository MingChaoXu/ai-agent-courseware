"""
Patient Database API - CRUD + Vitals + Medications + Diagnoses + Timeline Analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any, List

router = APIRouter(prefix="/patients", tags=["patients"])

# Import DB (lazy to avoid circular import issues at startup)
_db = None

def _get_db():
    global _db
    if _db is None:
        from db.database import (
            create_patient, list_patients, get_patient, update_patient, delete_patient,
            add_visit, get_visits, get_visit, delete_visit,
            add_vital_sign, get_vital_signs, get_vital_trends, delete_vital_sign,
            add_medication, get_medications, stop_medication, delete_medication,
            add_diagnosis, get_diagnoses, resolve_diagnosis,
            get_patient_summary, get_patient_timeline_text,
            VITAL_METRICS,
        )
        _db = {
            "create_patient": create_patient, "list_patients": list_patients,
            "get_patient": get_patient, "update_patient": update_patient,
            "delete_patient": delete_patient, "add_visit": add_visit,
            "get_visits": get_visits, "get_visit": get_visit,
            "delete_visit": delete_visit, "get_timeline_text": get_patient_timeline_text,
            "add_vital_sign": add_vital_sign, "get_vital_signs": get_vital_signs,
            "get_vital_trends": get_vital_trends, "delete_vital_sign": delete_vital_sign,
            "add_medication": add_medication, "get_medications": get_medications,
            "stop_medication": stop_medication, "delete_medication": delete_medication,
            "add_diagnosis": add_diagnosis, "get_diagnoses": get_diagnoses,
            "resolve_diagnosis": resolve_diagnosis,
            "get_patient_summary": get_patient_summary,
            "VITAL_METRICS": VITAL_METRICS,
        }
    return _db


# ============================================================
# Request Models
# ============================================================

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

class VitalSignRequest(BaseModel):
    patient_id: int
    metric: str = Field(..., description="Key in VITAL_METRICS: systolic_bp, fasting_glucose, hba1c, etc.")
    value: float
    unit: str = Field("")
    measure_date: str = Field("")
    source: str = Field("manual")

class MedicationAddRequest(BaseModel):
    patient_id: int
    drug_name: str
    dosage: str = ""
    frequency: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = True
    notes: str = ""

class DiagnosisAddRequest(BaseModel):
    patient_id: int
    diagnosis_name: str
    icd_code: str = ""
    is_chronic: bool = False
    diagnosed_date: str = ""
    status: str = "active"
    notes: str = ""

class TimelineAnalysisRequest(BaseModel):
    patient_id: int


# ============================================================
# Patient Endpoints
# ============================================================

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


@router.get("/{patient_id}/summary")
async def api_patient_summary(patient_id: int):
    """Get comprehensive patient summary (visits, vitals, meds, diagnoses)."""
    db = _get_db()
    summary = db["get_patient_summary"](patient_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Patient not found")
    return summary


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
    """Delete a patient and all their records."""
    db = _get_db()
    ok = db["delete_patient"](patient_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"status": "deleted"}


# ============================================================
# Visit Endpoints
# ============================================================

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


# ============================================================
# Vital Signs Endpoints
# ============================================================

@router.get("/vital-metrics")
async def api_vital_metrics():
    """Get available vital metric definitions (for frontend dropdowns)."""
    db = _get_db()
    return db["VITAL_METRICS"]


@router.get("/{patient_id}/vitals")
async def api_get_vitals(patient_id: int, metric: str = None):
    """Get vital signs for a patient, optionally filtered by metric."""
    db = _get_db()
    return db["get_vital_signs"](patient_id, metric)


@router.get("/{patient_id}/vital-trends")
async def api_vital_trends(patient_id: int):
    """Get all vital sign trends grouped by metric (for charting)."""
    db = _get_db()
    return db["get_vital_trends"](patient_id)


@router.post("/vitals")
async def api_add_vital(req: VitalSignRequest):
    """Add a vital sign measurement."""
    db = _get_db()
    patient = db["get_patient"](req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db["add_vital_sign"](
        req.patient_id, req.metric, req.value,
        unit=req.unit, measure_date=req.measure_date, source=req.source
    )


@router.delete("/vitals/{vital_id}")
async def api_delete_vital(vital_id: int):
    """Delete a vital sign record."""
    db = _get_db()
    ok = db["delete_vital_sign"](vital_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Vital sign not found")
    return {"status": "deleted"}


# ============================================================
# Medication Endpoints
# ============================================================

@router.get("/{patient_id}/medications")
async def api_get_medications(patient_id: int, current_only: bool = False):
    """Get medications for a patient."""
    db = _get_db()
    return db["get_medications"](patient_id, current_only)


@router.post("/medications")
async def api_add_medication(req: MedicationAddRequest):
    """Add a medication for a patient."""
    db = _get_db()
    patient = db["get_patient"](req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db["add_medication"](
        req.patient_id, req.drug_name, req.dosage, req.frequency,
        req.start_date, req.end_date, req.is_current, req.notes
    )


@router.put("/medications/{med_id}/stop")
async def api_stop_medication(med_id: int):
    """Stop (discontinue) a medication."""
    db = _get_db()
    result = db["stop_medication"](med_id)
    if not result:
        raise HTTPException(status_code=404, detail="Medication not found")
    return result


@router.delete("/medications/{med_id}")
async def api_delete_medication(med_id: int):
    """Delete a medication record."""
    db = _get_db()
    ok = db["delete_medication"](med_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Medication not found")
    return {"status": "deleted"}


# ============================================================
# Diagnosis Endpoints
# ============================================================

@router.get("/{patient_id}/diagnoses")
async def api_get_diagnoses(patient_id: int, active_only: bool = False):
    """Get diagnoses for a patient."""
    db = _get_db()
    return db["get_diagnoses"](patient_id, active_only)


@router.post("/diagnoses")
async def api_add_diagnosis(req: DiagnosisAddRequest):
    """Add a diagnosis for a patient."""
    db = _get_db()
    patient = db["get_patient"](req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db["add_diagnosis"](
        req.patient_id, req.diagnosis_name, req.icd_code,
        req.is_chronic, req.diagnosed_date, req.status, req.notes
    )


@router.put("/diagnoses/{diag_id}/resolve")
async def api_resolve_diagnosis(diag_id: int):
    """Resolve (mark as inactive) a diagnosis."""
    db = _get_db()
    result = db["resolve_diagnosis"](diag_id)
    if not result:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return result


# ============================================================
# Timeline Analysis
# ============================================================

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

    # Auto-archive the analysis as a visit
    if result.get("answer") and not result.get("error"):
        try:
            db["add_visit"](req.patient_id, "timeline", "AI时序病情分析", result["answer"])
        except Exception:
            pass

    return {"patient": patient, "timeline_text": timeline_text, "analysis": result}
