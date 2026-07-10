"""
Precision Marketing RFM Analysis - Structured Output Agent
Uses PydanticOutputParser to get structured JSON from LLM.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from config import settings


class CustomerProfile(BaseModel):
    """Structured output model."""
    customer_id: str = Field(description="客户ID")
    rfm_segment: str = Field(description="RFM分群：高价值客户/成长客户/流失风险客户/沉睡客户")
    consumption_preference: str = Field(description="消费偏好分析")
    shopping_habit: str = Field(description="购物习惯分析")
    marketing_strategy: str = Field(description="个性化营销策略")
    expected_roi: str = Field(description="预期ROI（投入产出比）")


def create_agent():
    """Create and return the analysis chain."""
    if not settings.is_configured():
        return None

    parser = PydanticOutputParser(pydantic_object=CustomerProfile)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个精准营销分析助手，帮助营销人员分析客户数据，制定个性化营销策略。

分析维度：
1. RFM分群（最近消费R、消费频率F、消费金额M）
2. 消费偏好分析
3. 购物习惯分析
4. 个性化营销策略
5. 预期ROI\n\n{format_instructions}"""),
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
