"""
Construction Document Generation - Document Generation Agent
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


def create_agent():
    if not settings.is_configured():
        return None

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个施工文档生成助手，帮助工程项目人员快速生成规范的施工文档。

生成要求：
1. 严格按照工程文档规范格式
2. 包含工程概况、施工方案、安全措施、质量控制等章节
3. 使用专业工程术语
4. 安全措施必须具体可执行"""),
        ("human", "请根据以下信息生成文档：\n{input_text}"),
    ])

    return prompt | llm | StrOutputParser()


def chat(agent, question: str) -> Dict[str, Any]:
    try:
        answer = agent.invoke({"input_text": question})
        return {"answer": answer, "error": None}
    except Exception as e:
        return {"answer": None, "error": f"Error: {str(e)}"}
