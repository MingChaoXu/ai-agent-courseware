"""
Contract Risk Intelligent Audit - Structured Output Agent
Uses PydanticOutputParser to get structured JSON from LLM.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from config import settings


class ContractAuditResult(BaseModel):
    """Structured output model."""
    overall_risk_level: str = Field(description="整体风险等级：低风险/中风险/高风险")
    risk_items: str = Field(description="风险条款列表，每项包含条款内容、风险类型、风险等级、修改建议")
    missing_clauses: str = Field(description="缺失条款建议，如保密条款、知识产权条款等")
    recommendations: str = Field(description="综合审查建议")
    summary: str = Field(description="审查总结")


def create_agent():
    """Create and return the analysis chain."""
    if not settings.is_configured():
        return None

    parser = PydanticOutputParser(pydantic_object=ContractAuditResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个合同风险审查助手，帮助法务人员快速识别合同中的风险条款。

审查维度：
1. 违约责任是否对等
2. 付款条件是否存在风险
3. 知识产权归属是否明确
4. 争议解决条款是否合理
5. 保密条款是否完善
6. 终止条款是否公平\n\n{format_instructions}"""),
        ("human", "{input_text}"),
    ]).partial(format_instructions=parser.get_format_instructions())

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )

    chain = prompt | llm | parser
    return {"chain": chain, "parser": parser, "fallback_chain": prompt | llm | StrOutputParser()}


def analyze(agent, input_text: str) -> Dict[str, Any]:
    """Run analysis on input text."""
    try:
        result = agent["chain"].invoke({"input_text": input_text})
        return {"answer": result.model_dump(), "error": None}
    except Exception as e:
        try:
            text_result = agent["fallback_chain"].invoke({"input_text": input_text})
            return {"answer": text_result, "error": None}
        except Exception as e2:
            return {"answer": None, "error": f"Analysis failed: {str(e2)}"}
