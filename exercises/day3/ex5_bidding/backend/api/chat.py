"""
Chat/Analysis API
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])

# Global agent instance (initialized in main.py)
agent_instance = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Analyze input text and return structured result."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check API configuration.")

    try:
        from agent.agent import analyze
        result = analyze(agent_instance, request.question)
        return ChatResponse(answer=result["answer"], error=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
