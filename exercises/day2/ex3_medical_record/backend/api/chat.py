"""
Medical AI Assistant API - 4 modules
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from typing import Optional

router = APIRouter(tags=["chat"])

# Global agent instance (initialized in main.py)
agent_instance = None

VALID_MODULES = ["record", "lab", "treatment", "qc"]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Analyze input text and return structured result.

    The 'module' field in request selects which analysis to run:
    - 'record': 门诊病历生成
    - 'lab': 检验报告解读
    - 'treatment': 诊疗方案推荐
    - 'qc': 病历质控校验
    """
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check API configuration.")

    module = getattr(request, "module", "record") or "record"
    if module not in VALID_MODULES:
        raise HTTPException(status_code=400, detail=f"Invalid module: {module}. Valid: {VALID_MODULES}")

    try:
        from agent.agent import analyze
        result = analyze(agent_instance, module, request.question)
        return ChatResponse(answer=result["answer"], error=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
