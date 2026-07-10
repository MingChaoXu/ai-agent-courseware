"""
Prompt Ablation Experiment - Comparison Agent
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


COMPARISON_DATA = [
    {"name": "完整Prompt", "desc": "包含角色+规则+示例+格式", "pros": "输出质量最佳", "cons": "Token消耗大"},
    {"name": "无角色设定", "desc": "去掉System Prompt角色描述", "pros": "节省Token", "cons": "输出风格不稳定"},
    {"name": "无Few-shot", "desc": "去掉示例", "pros": "更灵活", "cons": "格式遵循度下降"},
    {"name": "无格式约束", "desc": "去掉输出格式要求", "pros": "自由度高", "cons": "输出不可控"}
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
        ("system", """你是一个Prompt工程教学助手，帮助学习者理解Prompt各组件的作用和重要性。"""),
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
