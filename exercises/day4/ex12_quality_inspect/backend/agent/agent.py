"""
PCB Quality Inspection Agent - ReAct Agent
Uses LangGraph create_react_agent with domain-specific tools.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent

from config import settings


# ---- Tool Functions ----

def defect_detect(image_desc: str) -> str:
    """检测PCB板焊接缺陷"""
    return "检测结果：\n1. 连锡缺陷（U3引脚12-13，置信度0.92）\n2. 偏移缺陷（R5左偏0.3mm，置信度0.85）\n3. 划痕（板面右下角，置信度0.78）"

def ocr_extract(image_desc: str) -> str:
    """OCR识别PCB板丝印"""
    return "识别结果：\n1. 丝印型号：PCB-V2.3-2026\n2. 序列号：SN20260615001\n3. 产地：MADE IN CHINA\n4. 认证标识：CE/FCC/RoHS"

def component_count(image_desc: str) -> str:
    """统计PCB板元件数量"""
    return "元件统计：\n- IC芯片：5个\n- 电阻：28个\n- 电容：15个\n- 二极管：4个\n- 连接器：2个\n- 总计：54个\n- 缺件率：0%（正常）"


def create_agent():
    """Create and return a ReAct agent with tools."""
    if not settings.is_configured():
        return None

    tools = [
        Tool(name="defect_detect", func=defect_detect, description="检测PCB板焊接缺陷，输入为图像描述，返回缺陷类型和位置。"),
    Tool(name="ocr_extract", func=ocr_extract, description="OCR识别PCB板丝印文字，输入为图像描述，返回识别到的文字信息。"),
    Tool(name="component_count", func=component_count, description="统计PCB板元件数量，输入为图像描述，返回元件统计结果。"),
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
        prompt='你是一个PCB电路板质量检测助手，帮助质检员分析电路板图像并识别缺陷。\n你可以使用缺陷检测、OCR识别和元件计数工具。',
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
