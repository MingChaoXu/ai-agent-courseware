"""
Context Compression Strategy - Comparison Agent
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


COMPARISON_DATA = [
    {"name": "BufferMemory", "desc": "保留完整历史(不压缩)", "pros": "信息完整", "cons": "Token消耗大"},
    {"name": "SummaryMemory", "desc": "LLM自动摘要压缩", "pros": "保留要点,节省Token", "cons": "细节可能丢失,有额外LLM调用成本"},
    {"name": "滑动窗口", "desc": "只保留最近K轮对话", "pros": "零成本,零延迟,实现简单", "cons": "早期重要信息可能被丢弃"}
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
        ("system", """你是一个AI技术教学助手，帮助学习者理解LLM上下文管理和压缩策略。"""),
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
