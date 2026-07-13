"""
Medical AI Assistant API - 5 modules + auto-archiving
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from typing import Optional

router = APIRouter(tags=["chat"])

# Global agent instance (initialized in main.py)
agent_instance = None

VALID_MODULES = ["record", "lab", "treatment", "qc", "timeline"]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Analyze input text and return structured result.

    The 'module' field selects which analysis to run:
    - 'record': 门诊病历生成
    - 'lab': 检验报告解读
    - 'treatment': 诊疗方案推荐
    - 'qc': 病历质控校验
    - 'timeline': 时序病情分析 (usually called via /api/patients/timeline-analysis)

    Optional 'patient_id' will archive the result to that patient's record.
    """
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check API configuration.")

    module = getattr(request, "module", "record") or "record"
    if module not in VALID_MODULES:
        raise HTTPException(status_code=400, detail=f"Invalid module: {module}. Valid: {VALID_MODULES}")

    try:
        from agent.agent import analyze
        result = analyze(agent_instance, module, request.question)

        # Auto-archive to patient if patient_id provided
        patient_id = getattr(request, "patient_id", None)
        if patient_id and result.get("answer") and not result.get("error"):
            try:
                from db.database import add_visit, get_patient
                if get_patient(patient_id):
                    add_visit(patient_id, module, request.question, result["answer"])
            except Exception:
                pass  # Archiving failure should not block the response

        return ChatResponse(answer=result["answer"], error=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
