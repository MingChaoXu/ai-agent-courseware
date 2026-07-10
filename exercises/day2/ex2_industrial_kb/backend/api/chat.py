"""
Chat API - RAG conversation endpoint
"""

import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, SourceDocument

router = APIRouter(tags=["chat"])
agent_instance = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized.")
    try:
        from agent.agent import chat as agent_chat
        conv_id = request.conversation_id or str(uuid.uuid4())
        result = agent_chat(agent_instance, request.question, conv_id)
        return ChatResponse(
            answer=result["answer"],
            sources=[SourceDocument(**s) for s in result.get("sources", [])],
            conversation_id=result.get("conversation_id", conv_id),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
