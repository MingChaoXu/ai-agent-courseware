"""
Agent Ablation Evaluation - Comparison Agent
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


COMPARISON_DATA = [
    {"name": "完整Agent", "desc": "所有组件齐全（baseline）", "pros": "性能最优", "cons": "成本最高"},
    {"name": "去除SystemPrompt", "desc": "去掉系统提示词", "pros": "节省Token", "cons": "输出质量下降明显"},
    {"name": "去除工具描述", "desc": "去掉工具描述信息", "pros": "减少Token", "cons": "工具调用准确率下降"},
    {"name": "非正式语气", "desc": "系统提示改为口语化", "pros": "更自然", "cons": "专业性和规范性下降"}
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
        ("system", """你是一个AI Agent评估分析助手，帮助研究者设计和执行消融实验，评估Agent各组件的贡献度。"""),
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
