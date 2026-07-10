"""
Pydantic request/response schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None


class SourceDocument(BaseModel):
    content: str
    score: float = 0.0


class ChatResponse(BaseModel):
    answer: str = ""
    sources: List[SourceDocument] = Field(default_factory=list)
    conversation_id: str = ""
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    agent_ready: bool


# Knowledge Base schemas
class KbDocument(BaseModel):
    id: str
    title: str
    chunks: int


class KbListResponse(BaseModel):
    documents: List[KbDocument] = Field(default_factory=list)
    total_chunks: int = 0


class KbUploadResponse(BaseModel):
    status: str
    title: str
    chunks: int


class KbSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=10)


class KbSearchResponse(BaseModel):
    results: List[SourceDocument] = Field(default_factory=list)
