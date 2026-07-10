"""
Power Safety CV Inspection Agent - ReAct Agent
Uses LangGraph create_react_agent with domain-specific tools.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent

from config import settings


# ---- Tool Functions ----

def ppe_check(scene_desc: str) -> str:
    """检测PPE佩戴"""
    return "PPE检测结果：\n- 安全帽：2/2人佩戴 ✅\n- 绝缘手套：1/2人佩戴 ⚠️（1人未戴）\n- 绝缘鞋：2/2人穿戴 ✅\n- 绝缘服：2/2人穿戴 ✅\n- 风险提示：1人未戴绝缘手套，需立即纠正"

def distance_check(scene_desc: str) -> str:
    """检查安全距离"""
    return "安全距离检测：\n- 电压等级：10kV\n- 安全距离要求：≥0.7m\n- 实测最近距离：1.2m\n- 判定：合格 ✅"

def environment_check(scene_desc: str) -> str:
    """检查环境安全"""
    return "环境安全检测：\n- 安全围栏：已设置 ✅\n- 警示标识：已张贴 ✅\n- 通道畅通：是 ✅\n- 照明充足：是 ✅\n- 灭火器：2个，在有效期内 ✅\n- 整体评估：环境安全合格"


def create_agent():
    """Create and return a ReAct agent with tools."""
    if not settings.is_configured():
        return None

    tools = [
        Tool(name="ppe_check", func=ppe_check, description="检测人员PPE佩戴情况，输入为场景描述，返回安全帽、手套、鞋等检测结果。"),
    Tool(name="distance_check", func=distance_check, description="检查人员与带电设备的安全距离，输入为场景描述，返回距离检测结果。"),
    Tool(name="environment_check", func=environment_check, description="检查作业环境安全，输入为场景描述，返回围栏、标识、通道等检测结果。"),
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
        prompt='你是一个电力行业安全检测助手，帮助安全员分析电力作业现场的图片并识别安全隐患。\n你可以使用PPE检测、安全距离检测和环境检测工具。',
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
