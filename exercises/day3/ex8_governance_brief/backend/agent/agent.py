"""
Governance Brief Generation - Structured Output Agent
Uses PydanticOutputParser to get structured JSON from LLM.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from config import settings


class GovernanceBrief(BaseModel):
    """Structured output model."""
    title: str = Field(description="通报标题")
    category: str = Field(description="事件类别：突发事件/日常工作/政策通知/其他")
    background: str = Field(description="事由背景")
    process: str = Field(description="处理经过")
    result: str = Field(description="处理结果")
    follow_up: str = Field(description="后续措施")
    policy_basis: str = Field(description="政策依据")


def create_agent():
    """Create and return the analysis chain."""
    if not settings.is_configured():
        return None

    parser = PydanticOutputParser(pydantic_object=GovernanceBrief)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个政务通报生成助手，帮助政府工作人员快速生成规范的政务通报文件。

生成要求：
1. 严格按照政务通报格式
2. 语言正式、简洁
3. 包含事由、经过、处理结果、后续措施
4. 数据准确，引用政策依据\n\n{format_instructions}"""),
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
