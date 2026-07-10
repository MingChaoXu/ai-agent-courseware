"""
HR Policy Intelligent Review - Structured Output Agent
Uses PydanticOutputParser to get structured JSON from LLM.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from config import settings


class HRReviewResult(BaseModel):
    """Structured output model."""
    compliance_status: str = Field(description="合规状态：合规/部分合规/不合规")
    issues: str = Field(description="发现的问题列表，每项包含条款、问题类型、风险等级、修改建议")
    missing_items: str = Field(description="制度缺失项建议")
    recommendations: str = Field(description="综合改进建议")
    summary: str = Field(description="审查总结")


def create_agent():
    """Create and return the analysis chain."""
    if not settings.is_configured():
        return None

    parser = PydanticOutputParser(pydantic_object=HRReviewResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个人事制度审查助手，帮助HR部门快速审查公司人事制度的合规性和完整性。

审查维度：
1. 劳动法合规性
2. 制度完整性
3. 条款公平性
4. 操作可行性
5. 风险条款识别\n\n{format_instructions}"""),
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
