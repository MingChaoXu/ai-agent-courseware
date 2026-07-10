"""
Chat API - RAG-based conversation endpoint
"""

import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, SourceDocument
from config import settings

router = APIRouter(tags=["chat"])

# Global RAG chain instance (initialized in main.py)
rag_chain = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a question to the Gov QA agent.

    Returns the answer along with source documents used for retrieval.
    """
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG chain not initialized")

    if not rag_chain._kb.is_loaded:
        raise HTTPException(status_code=503, detail="Knowledge base not loaded")

    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        result = rag_chain.chat(
            question=request.question,
            conversation_id=conversation_id,
        )
        return ChatResponse(
            answer=result["answer"],
            sources=[SourceDocument(**s) for s in result["sources"]],
            conversation_id=result["conversation_id"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.delete("/chat/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history."""
    if rag_chain:
        rag_chain.clear_conversation(conversation_id)
    return {"status": "ok"}
