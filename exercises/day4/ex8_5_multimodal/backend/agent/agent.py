"""
Multimodal Processing Mode Comparison - Comparison Agent
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


COMPARISON_DATA = [
    {"name": "NATIVE模式", "desc": "直接多模态输入到GPT-4o", "pros": "端到端,信息损失小", "cons": "成本高,延迟大"},
    {"name": "EXTRACT模式", "desc": "OCR/检测转文本后再给LLM", "pros": "成本低,可复用", "cons": "信息有损失"},
    {"name": "TOOL模式", "desc": "Agent调用专业视觉工具", "pros": "灵活可控,可扩展", "cons": "架构复杂"}
]


def create_agent():
    """Create LLM chain for answering questions."""
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
        ("system", """你是一个多模态AI技术教学助手，帮助学习者理解多模态信息处理的不同方式。"""),
        ("human", "{question}"),
    ])

    return prompt | llm | StrOutputParser()


def chat(agent, question: str) -> Dict[str, Any]:
    """Answer question using LLM with comparison context."""
    context = "\n".join([
        f"- {c['name']}: {c['desc']} | 优势: {c['pros']} | 劣势: {c['cons']}"
        for c in COMPARISON_DATA
    ])
    try:
        answer = agent.invoke({"question": f"参考信息:\n{context}\n\n问题: {question}"})
        return {"answer": answer, "error": None}
    except Exception as e:
        return {"answer": None, "error": f"Error: {str(e)}"}
