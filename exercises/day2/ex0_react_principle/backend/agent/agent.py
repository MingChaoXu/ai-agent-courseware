"""
ReAct Reasoning Principle - ReAct Agent
Uses LangGraph create_react_agent with domain-specific tools.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent

from config import settings


# ---- Tool Functions ----

def search_policy(query: str) -> str:
    """搜索政务政策信息"""
    mock_data = {
        "户口": "户口迁移需满足：1)合法稳定住所；2)参加社保满3年；3)无犯罪记录。办理地点：辖区派出所户籍窗口。",
        "社保": "社保转移流程：1)原参保地开具参保凭证；2)新参保地提交转移申请；3)45个工作日内完成转移。线上可通过国家社会保险公共服务平台办理。",
        "公积金": "公积金提取条件：购房、租房、退休、离职等。购房提取额度为账户余额的90%。",
        "居住证": "居住证申领条件：居住满半年，有合法稳定就业或住所。到居住地派出所办理。",
    }
    for key, value in mock_data.items():
        if key in query:
            return value
    return f"未找到与 '{query}' 直接相关的结果，建议缩小搜索范围。"

def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        allowed = set("0123456789+-*/().% ")
        if all(c in allowed for c in expression):
            return f"计算结果: {eval(expression)}"
        return "表达式包含不允许的字符"
    except Exception:
        return "计算错误，请检查表达式格式"


def create_agent():
    """Create and return a ReAct agent with tools."""
    if not settings.is_configured():
        return None

    tools = [
        Tool(name="search_policy", func=search_policy, description="搜索政务政策信息，输入为搜索关键词，返回相关政策内容。适用于户口、社保、公积金等政务咨询。"),
    Tool(name="calculate", func=calculate, description="计算数学表达式，输入为合法的数学表达式字符串，返回计算结果。例如 '2026-2018'。"),
    ]

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )

    agent = create_react_agent(
        llm,
        tools=tools,
        prompt='你是一个政务咨询助手，请使用工具回答用户问题。\n你可以使用搜索和计算工具来获取信息。\n请按照 Thought → Action → Observation 的循环推理，直到得出最终答案。',
    )
    return agent


def chat(agent, question: str) -> Dict[str, Any]:
    """Run the agent on a question."""
    try:
        result = agent.invoke({"messages": [("user", question)]})
        answer = result["messages"][-1].content
        return {"answer": answer, "error": None}
    except Exception as e:
        return {"answer": None, "error": f"Agent error: {str(e)}"}
