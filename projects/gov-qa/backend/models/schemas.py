"""
Pydantic request/response schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ---------- Chat ----------

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for multi-turn")


class SourceDocument(BaseModel):
    content: str = Field(..., description="Retrieved document content")
    score: float = Field(0.0, description="Similarity score")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="LLM generated answer")
    sources: List[SourceDocument] = Field(default_factory=list, description="Retrieved sources")
    conversation_id: str = Field("", description="Conversation ID")


# ---------- Knowledge Base ----------

class KbUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Document title")
    content: str = Field(..., min_length=1, description="Document text content")
    chunk_size: int = Field(500, description="Chunk size for text splitting")


class KbUploadResponse(BaseModel):
    status: str = "ok"
    title: str
    chunks: int


class KbDocument(BaseModel):
    id: str
    title: str
    chunks: int


class KbListResponse(BaseModel):
    documents: List[KbDocument]
    total_chunks: int


class KbSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(5, description="Number of results to return")


class KbSearchResponse(BaseModel):
    results: List[SourceDocument]


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    embedding_configured: bool
    knowledge_base_loaded: bool
    total_chunks: int
