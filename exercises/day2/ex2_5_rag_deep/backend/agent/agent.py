"""
RAG Principle Deep Dive - Comparison Agent
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


COMPARISON_DATA = [
    {"name": "稀疏检索(BM25)", "desc": "关键词TF-IDF匹配", "pros": "精确术语匹配强", "cons": "无法理解同义词"},
    {"name": "稠密检索", "desc": "语义向量相似度", "pros": "模糊语义匹配强", "cons": "精确术语可能漏"},
    {"name": "混合检索", "desc": "两路融合+重排序", "pros": "兼顾精确和模糊", "cons": "计算成本更高"}
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
        ("system", """你是一个RAG技术教学助手，帮助学习者理解检索增强生成的工作原理。
请清晰解释Embedding、向量检索、稠密检索vs稀疏检索等概念。"""),
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
