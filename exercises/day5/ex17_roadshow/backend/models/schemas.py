"""
Pydantic request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str = ""
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    agent_ready: bool
