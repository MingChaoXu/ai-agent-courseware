"""Chat API - main agent interaction endpoint."""
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from db import database as db

router = APIRouter(tags=["chat"])
agent_instance = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check LLM config.")
    try:
        from agent.agent import chat as agent_chat
        result = agent_chat(agent_instance, request.question, force_agent=request.agent)

        # Save to history
        db.add_chat_message("user", request.question)
        db.add_chat_message("assistant", result.get("answer", ""), result.get("agent_used", ""))

        return ChatResponse(
            answer=result.get("answer", ""),
            agent_used=result.get("agent_used"),
            cv_results=result.get("cv_results"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.get("/chat/history")
async def get_history(limit: int = 20):
    return db.get_chat_history(limit)
