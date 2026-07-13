"""
Pydantic request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Input text for analysis")
    module: Optional[str] = Field("record", description="Analysis module: record/lab/treatment/qc/timeline")
    patient_id: Optional[int] = Field(None, description="If set, archive result to this patient's record")


class ChatResponse(BaseModel):
    answer: Any = Field(None, description="Analysis result (structured JSON or text)")
    error: Optional[str] = Field(None, description="Error message if any")


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    agent_ready: bool
    modules: list = Field(default_factory=list, description="Available modules")
