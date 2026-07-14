"""
Pydantic request schemas for Consumer AI Ops Platform API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class BIChatRequest(BaseModel):
    question: str = Field(..., description="自然语言分析问题")
    session_id: Optional[str] = None


class CSChatRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    session_id: Optional[str] = None


class PersonaRequest(BaseModel):
    customer_id: str = Field(..., description="客户ID，如C001")


class SentimentRequest(BaseModel):
    category: Optional[str] = Field(None, description="过滤品类")


class StrategyRequest(BaseModel):
    segment: Optional[str] = Field("高价值沉睡", description="目标客群")
    objective: Optional[str] = Field("提升客户活跃度和复购率", description="营销目标")


class ROISimulateRequest(BaseModel):
    budget: float = Field(50000, description="总预算（元）")
    target_segment: Optional[str] = Field("高价值沉睡", description="目标客群")
    channel_mix: Optional[dict] = Field(None, description="渠道配比")
