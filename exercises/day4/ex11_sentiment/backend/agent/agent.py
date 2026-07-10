"""
Financial Sentiment Analysis - Structured Output Agent
Uses PydanticOutputParser to get structured JSON from LLM.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from config import settings


class SentimentReport(BaseModel):
    """Structured output model."""
    overall_sentiment: str = Field(description="整体舆情倾向：正面/负面/中性")
    red_count: str = Field(description="红色预警条数")
    yellow_count: str = Field(description="黄色关注条数")
    green_count: str = Field(description="绿色正常条数")
    hot_topics: str = Field(description="热点话题列表")
    items: str = Field(description="逐条分析结果，包含内容、情感、评分、风险等级、关键话题、建议行动")
    summary: str = Field(description="舆情总结和建议")


def create_agent():
    """Create and return the analysis chain."""
    if not settings.is_configured():
        return None

    parser = PydanticOutputParser(pydantic_object=SentimentReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个金融舆情分析助手，帮助金融机构监测和分析社交媒体上的舆情信息。

分析维度：
1. 逐条情感分析（正面/负面/中性）
2. 风险等级评估（红/黄/绿）
3. 热点话题识别
4. 舆情趋势判断
5. 应对建议\n\n{format_instructions}"""),
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
