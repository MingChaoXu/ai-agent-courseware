"""
MCP Protocol Demo Agent - ReAct Agent
Uses LangGraph create_react_agent with domain-specific tools.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent

from config import settings


# ---- Tool Functions ----

def web_search(query: str) -> str:
    """搜索网络信息"""
    return f"搜索 '{query}' 结果：\n1. [MCP协议官方文档] Model Context Protocol是一种标准化Agent工具调用协议...\n2. [技术博客] MCP支持三类工具：感知、执行、协作...\n3. [GitHub] langchain-mcp适配器已发布..."

def code_execute(code: str) -> str:
    """执行代码"""
    try:
        result = eval(code, {"__builtins__": {"abs": abs, "sum": sum, "len": len, "round": round, "max": max, "min": min}})
        return f"执行结果: {result}"
    except Exception as e:
        return f"执行错误: {e}"

def send_notification(content: str) -> str:
    """发送通知"""
    return f"通知已发送：'{content[:50]}...' → 接收人：审批管理员 → 状态：已送达 ✅"


def create_agent():
    """Create and return a ReAct agent with tools."""
    if not settings.is_configured():
        return None

    tools = [
        Tool(name="web_search", func=web_search, description="搜索网络信息（感知类工具），输入搜索关键词，返回搜索结果摘要。"),
    Tool(name="code_execute", func=code_execute, description="执行代码（执行类工具），输入Python代码，返回执行结果。"),
    Tool(name="send_notification", func=send_notification, description="发送通知（协作类工具），输入通知内容，返回发送状态。"),
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
        prompt='你是一个MCP协议演示助手，帮助学习者理解Model Context Protocol的工具发现和调用机制。\n你可以使用感知类、执行类和协作类工具。',
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
