"""
Chat API - Agent conversation endpoint
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])

# Global agent instance (initialized in main.py)
agent_instance = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a question to the agent."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check API configuration.")

    try:
        from agent.agent import chat as agent_chat
        result = agent_chat(agent_instance, request.question)
        if result.get("error"):
            return ChatResponse(answer="", error=result["error"])
        return ChatResponse(answer=result["answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
