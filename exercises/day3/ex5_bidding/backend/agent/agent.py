"""
Bidding Document Intelligent Analysis - Structured Output Agent
Uses PydanticOutputParser to get structured JSON from LLM.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from config import settings


class BiddingAnalysisResult(BaseModel):
    """Structured output model."""
    project_info: str = Field(description="项目基本信息：名称、编号、预算金额")
    qualification_req: str = Field(description="投标人资格要求清单")
    technical_summary: str = Field(description="技术要求摘要")
    scoring_criteria: str = Field(description="评分标准分析")
    deadline_info: str = Field(description="投标截止时间、地点、方式")
    risk_alerts: str = Field(description="风险提示清单")
    recommendations: str = Field(description="投标建议")


def create_agent():
    """Create and return the analysis chain."""
    if not settings.is_configured():
        return None

    parser = PydanticOutputParser(pydantic_object=BiddingAnalysisResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个招标文件分析助手，帮助投标人快速理解招标要求，识别关键信息。

分析维度：
1. 项目基本信息（项目名称、编号、预算）
2. 投标人资格要求
3. 技术要求摘要
4. 评分标准分析
5. 投标截止时间和地点
6. 风险提示\n\n{format_instructions}"""),
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
