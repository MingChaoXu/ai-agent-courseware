"""
课题12: 制造领域AI质量检测 — LangChain Agent + 多模态工具
=========================================================
使用 Agent + 视觉检测工具实现 PCB 板质量检测，
对比 NATIVE / EXTRACT_TO_TEXT / TOOL 三种多模态模式在质检场景的效果。

技术栈：LangChain 1.x / LangGraph（Tool, create_react_agent, LCEL Chain）
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent


# ============================================================
#  课题12: 制造领域AI质量检测 — LangChain Agent + 多模态工具
# ============================================================

def exercise12_run():
    print("=" * 60)
    print("课题12: 制造领域AI质量检测（Agent + 多模态工具）")
    print("=" * 60)

    print("\n--- 步骤1: 构建质量检测 LangChain Agent ---")
    print("""
质检 Agent 设计（TOOL模式）：
  ① 模拟视觉检测工具（defect_detect, ocr_extract, component_count）
  ② 包装为 Tool 对象
   ③ create_react_agent（LangGraph 版）

  三种多模态模式通过不同工具组合实现：
  - NATIVE：Agent 直接理解图片描述
  - EXTRACT：调用 ocr_extract 工具
  - TOOL：调用 defect_detect + component_count 工具
    """)

    # ---- 模拟视觉工具 ----
    def defect_detect(image_desc: str) -> str:
        """模拟缺陷检测工具"""
        return json.dumps({
            "桥接": [{"location": "U1-pin3", "confidence": 0.95},
                     {"location": "U1-pin7", "confidence": 0.91},
                     {"location": "U2-pin2", "confidence": 0.88}],
            "偏移": [{"location": "C3", "offset": "2mm", "confidence": 0.93}],
            "划伤": [{"location": "板面左侧", "length": "2cm", "confidence": 0.87}]
        }, ensure_ascii=False)

    def ocr_extract(image_desc: str) -> str:
        """模拟OCR提取工具"""
        return json.dumps({
            "丝印": "PCB-V3.2",
            "序列号": "SN20260708",
            "产地": "MADE IN CN"
        }, ensure_ascii=False)

    def component_count(image_desc: str) -> str:
        """模拟元件计数工具"""
        return json.dumps({
            "芯片": 1, "电容": 8, "电阻": 5, "连接器": 1,
            "总元件数": 15, "缺陷数": 5, "缺陷率": "33.3%"
        }, ensure_ascii=False)

    # ---- 包装为 Tool ----
    tools = [
        Tool(
            name="defect_detect",
            func=defect_detect,
            description="对PCB板图片进行缺陷检测，返回桥接、偏移、划伤等缺陷的检测结果（位置+置信度）。输入为图片描述。",
        ),
        Tool(
            name="ocr_extract",
            func=ocr_extract,
            description="对PCB板图片进行OCR文字提取，返回丝印、序列号等信息。输入为图片描述。",
        ),
        Tool(
            name="component_count",
            func=component_count,
            description="对PCB板图片进行元件计数，返回各类元件数量和缺陷率统计。输入为图片描述。",
        ),
    ]

    llm = get_llm(temperature=0)

    quality_prompt = (
        "你是一个AI质量检测助手，帮助工厂对产品外观进行自动缺陷检测。\n\n"
        "检测流程：\n"
        "1. 接收产品图片描述\n"
        "2. 使用工具进行缺陷检测、OCR提取和元件计数\n"
        "3. 综合分析并生成检测报告\n"
        "4. 判定合格/不合格\n\n"
        "常见缺陷类型：\n"
        "- 焊点缺陷：虚焊、桥接、冷焊、漏焊\n"
        "- 元件缺陷：偏移、缺件、极性反、损伤\n"
        "- 板面缺陷：划伤、污渍、镀层脱落\n\n"
        "判定标准：缺陷率>5%判定不合格，置信度<80%标记需人工复检"
    )

    agent = create_react_agent(llm, tools=tools, prompt=quality_prompt)

    # 步骤2: 三种多模态模式质检对比
    print("\n--- 步骤2: 三种多模态模式质检对比 ---")
    test_image = "PCB板：板面有3处焊点桥接，1个电容偏移2mm，板面有2cm划伤，丝印标注PCB-V3.2"

    print(f"\n测试图片描述: {test_image}")

    # NATIVE模式 — 直接 LCEL Chain 调用（无需工具）
    print("\n【NATIVE模式质检】")
    print("  → 图片直接送入LLM理解")
    native_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是AI质检助手。请基于图片描述直接分析产品缺陷。\n"
         "输出：检测结果 | 缺陷数量 | 缺陷明细 | 整体判定"),
        ("human", "请直接分析这张PCB板图片：{image_desc}。识别所有缺陷并给出检测结果。"),
    ])
    native_chain = native_prompt | llm | StrOutputParser()
    try:
        result = native_chain.invoke({"image_desc": test_image})
        print(f"  NATIVE检测结果:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [NATIVE模式失败: {e}]")

    # EXTRACT模式 — 先提取再分析
    print("\n【EXTRACT_TO_TEXT模式质检】")
    print("  → 先OCR/检测提取，再文本分析")
    extract_info = ocr_extract(test_image)
    extract_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是AI质检助手。基于以下OCR提取信息分析PCB板缺陷，判断是否合格。"),
        ("human", "OCR提取信息: {extract_data}\n\n请判断PCB板是否合格。"),
    ])
    extract_chain = extract_prompt | llm | StrOutputParser()
    try:
        result = extract_chain.invoke({"extract_data": extract_info})
        print(f"  EXTRACT检测结果:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [EXTRACT模式失败: {e}]")

    # TOOL模式 — Agent + 视觉工具
    print("\n【TOOL模式质检】")
    print("  → Agent调用专用视觉工具获取结构化结果")
    try:
        result = agent.invoke({
            "messages": [("user", f"请对以下PCB板进行全面质检：{test_image}。依次调用缺陷检测、OCR提取和元件计数工具，然后综合判定是否合格。")]
        })
        print(f"\n  TOOL检测报告:\n  {result['messages'][-1].content[:300]}...")
    except Exception as e:
        print(f"  Agent执行出错: {e}")
        # 降级：手动拼接工具结果 + LCEL Chain
        print("  降级为手动工具调用 + LCEL Chain...")
        tool_data = f"缺陷检测: {defect_detect(test_image)}\nOCR: {ocr_extract(test_image)}\n计数: {component_count(test_image)}"
        tool_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是AI质检助手。基于视觉工具返回的结构化结果生成检测报告并判定合格/不合格。"),
            ("human", "工具返回数据：\n{tool_data}\n\n请生成检测报告。"),
        ])
        tool_chain = tool_prompt | llm | StrOutputParser()
        try:
            result = tool_chain.invoke({"tool_data": tool_data})
            print(f"  [Chain模式] {result[:300]}...")
        except Exception as e2:
            print(f"  [Chain模式也失败: {e2}]")

    print("\n三种模式在质检场景的对比：")
    print("  NATIVE：能感知焊点颜色和光泽差异，但token成本高")
    print("  EXTRACT：准确提取丝印文字，但丢失焊点外观细节")
    print("  TOOL：结构化输出适合自动化流水线，可触发返工工单")
    print("  产线推荐：TOOL为主 + NATIVE复核疑难件")

    print("\n课题12完成！")


if __name__ == "__main__":
    exercise12_run()
