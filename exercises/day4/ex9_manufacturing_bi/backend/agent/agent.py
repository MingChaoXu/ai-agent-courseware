"""
Manufacturing BI Analysis Agent - ReAct Agent
Uses LangGraph create_react_agent with domain-specific tools.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent

from config import settings


# ---- Tool Functions ----

def query_production_data(query: str) -> str:
    """查询生产数据"""
    data = {
        "A线": {"6月产量": 12000, "良品率": 0.985, "设备": "CNC-001"},
        "B线": {"6月产量": 9500, "良品率": 0.972, "设备": "CNC-002"},
        "C线": {"6月产量": 15000, "良品率": 0.991, "设备": "CNC-003"},
    }
    result = []
    for line, info in data.items():
        if line in query or "全部" in query or "各" in query:
            result.append(f"{line}: 产量{info['6月产量']}件, 良品率{info['良品率']*100:.1f}%, 设备{info['设备']}")
    return "\n".join(result) if result else f"未找到匹配 '{query}' 的数据"

def execute_code(code: str) -> str:
    """执行Python代码进行数据分析"""
    import io, contextlib
    allowed_names = {"A线": {"产量": 12000, "良品率": 0.985}, "B线": {"产量": 9500, "良品率": 0.972}, "C线": {"产量": 15000, "良品率": 0.991}}
    safe_globals = {"__builtins__": {"abs": abs, "sum": sum, "len": len, "round": round, "min": min, "max": max, "print": print, "range": range, "list": list, "dict": dict, "data": allowed_names}}
    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, safe_globals)
        return f.getvalue().strip() or "执行完成（无输出）"
    except Exception as e:
        return f"执行错误: {e}"


def create_agent():
    """Create and return a ReAct agent with tools."""
    if not settings.is_configured():
        return None

    tools = [
        Tool(name="query_production_data", func=query_production_data, description="查询生产数据，输入为查询条件（如产线名称、月份等），返回生产数据。"),
    Tool(name="execute_code", func=execute_code, description="执行Python代码进行数据分析，输入为Python代码字符串，返回执行结果。"),
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
        prompt='你是一个制造业BI分析助手，帮助工厂管理人员分析生产数据。\n你可以使用数据查询和代码执行工具来分析生产数据并回答问题。',
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
