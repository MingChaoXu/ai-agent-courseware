"""
Pydantic request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Input text for analysis")


class ChatResponse(BaseModel):
    answer: Any = Field(None, description="Analysis result (structured JSON or text)")
    error: Optional[str] = Field(None, description="Error message if any")


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    agent_ready: bool
