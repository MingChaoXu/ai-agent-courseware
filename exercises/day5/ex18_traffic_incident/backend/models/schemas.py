"""
Pydantic request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="交通事件描述文本")


class ChatResponse(BaseModel):
    answer: str = ""
    results: Any = Field(None, description="分Agent结果字典")
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    agent_ready: bool
    amap_mode: str = Field("", description="online or offline")
    modules: list = Field(default_factory=list, description="Available agent modules")


class IncidentCreateRequest(BaseModel):
    description: str = Field(..., min_length=1)
    incident_type: str = Field("")
    location: str = Field("")
    severity: str = Field("")
    status: str = Field("pending")


class IncidentUpdateRequest(BaseModel):
    incident_type: Optional[str] = None
    location: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    ai_analysis: Optional[str] = None


class DispatchAddRequest(BaseModel):
    incident_id: int
    analysis_text: str
    dispatch_plan: str = ""
    publish_text: str = ""
    review_report: str = ""
