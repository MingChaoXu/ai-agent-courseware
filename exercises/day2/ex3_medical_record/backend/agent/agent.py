"""
Medical Record Structured Generation - Structured Output Agent
Uses PydanticOutputParser to get structured JSON from LLM.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from config import settings


class MedicalRecord(BaseModel):
    """Structured output model."""
    chief_complaint: str = Field(description="主诉：患者主要症状及持续时间")
    present_illness: str = Field(description="现病史：症状发生发展过程")
    past_history: str = Field(description="既往史：既往疾病、手术、过敏史")
    physical_examination: str = Field(description="体格检查：生命体征和阳性体征")
    preliminary_diagnosis: str = Field(description="初步诊断：根据病史和体征得出的诊断")
    treatment_plan: str = Field(description="处理意见：用药处方、检查建议、注意事项")


def create_agent():
    """Create and return the analysis chain."""
    if not settings.is_configured():
        return None

    parser = PydanticOutputParser(pydantic_object=MedicalRecord)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个门诊病历辅助生成助手，帮助基层医生快速生成规范的门诊病历。

生成规则：
1. 严格按照门诊病历规范格式生成
2. 使用规范医学术语，不使用口语化表达
3. 药品使用通用名，标注剂量、用法、频次
4. 需要进一步检查的，明确标注检查项目

重要：本助手仅辅助生成病历草稿，最终诊断和处方必须由执业医师确认签字。\n\n{format_instructions}"""),
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
