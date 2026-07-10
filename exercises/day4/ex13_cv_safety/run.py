"""
课题13: 能源领域CV安全助手 — Agent + 安全检测工具
==================================================
使用 Agent + 安全检测工具实现电力作业现场安全隐患识别，
对比 NATIVE / EXTRACT_TO_TEXT / TOOL 三种模式在安全场景的效果。

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
#  课题13: 能源领域CV安全助手 — Agent + 安全检测工具
# ============================================================

def exercise13_run():
    print("=" * 60)
    print("课题13: 能源领域CV安全助手（Agent + 安全检测工具）")
    print("=" * 60)

    print("\n--- 步骤1: 构建安全检测 LangChain Agent ---")

    # ---- 模拟安全检测工具 ----
    def ppe_check(scene_desc: str) -> str:
        """模拟PPE（个人防护装备）检测工具"""
        return json.dumps({
            "人员A": {"安全帽": "已佩戴", "绝缘手套": "未佩戴", "绝缘鞋": "已佩戴"},
            "人员B": {"安全帽": "已佩戴", "绝缘手套": "已佩戴", "绝缘鞋": "已佩戴"},
        }, ensure_ascii=False)

    def distance_check(scene_desc: str) -> str:
        """模拟安全距离检测工具"""
        return json.dumps({
            "电压等级": "10kV",
            "实测距离": "0.5m",
            "要求距离": "≥0.7m",
            "判定": "违规",
        }, ensure_ascii=False)

    def environment_check(scene_desc: str) -> str:
        """模拟环境检测工具"""
        return json.dumps({
            "围栏完整性": "3面/应4面",
            "警示标志": "有",
            "通道畅通": "否（杂物堵塞）",
        }, ensure_ascii=False)

    tools = [
        Tool(
            name="ppe_check",
            func=ppe_check,
            description="检测作业人员PPE（安全帽、绝缘手套、绝缘鞋、安全带等）佩戴情况。输入为场景描述。",
        ),
        Tool(
            name="distance_check",
            func=distance_check,
            description="检测作业人员与带电设备的安全距离是否合规。输入为场景描述。",
        ),
        Tool(
            name="environment_check",
            func=environment_check,
            description="检测作业环境安全（围栏、警示标志、通道等）。输入为场景描述。",
        ),
    ]

    llm = get_llm(temperature=0)

    safety_prompt = (
        "你是作业现场安全检测助手，帮助能源企业识别现场安全隐患。\n\n"
        "检测项目：\n"
        "1. 【个人防护装备】安全帽、绝缘手套、护目镜、安全带是否佩戴\n"
        "2. 【作业环境】围栏设置、警示标志、安全距离是否合规\n"
        "3. 【设备状态】接地线、绝缘工具、验电器是否正确使用\n\n"
        "风险分级：\n"
        "- 严重：未佩戴安全帽/绝缘手套、带电作业无防护 → 立即停工\n"
        "- 一般：围栏不完整、警示标志缺失 → 限期整改\n"
        "- 提示：工具摆放不规范、通道不畅 → 建议改进\n\n"
        "电力作业安全规程：\n"
        "- 安全距离：10kV≥0.7m，35kV≥1.0m，110kV≥1.5m\n"
        "- 高处作业≥2m必须使用安全带\n"
        "- 带电作业必须使用绝缘工具并有专人监护"
    )

    agent = create_react_agent(llm, tools=tools, prompt=safety_prompt)

    # 步骤2: 三种多模态模式安全检测对比
    print("\n--- 步骤2: 三种模式安全检测对比 ---")
    scene = "10kV配电室检修现场，2名作业人员，1人未戴绝缘手套，围栏缺少一面，0.5m处有非作业人员"

    print(f"\n场景描述: {scene}")

    # NATIVE模式
    print("\n【NATIVE模式 - 直接理解】")
    native_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是安全检测助手。基于现场描述直接判断所有安全隐患。\n电力规程：10kV安全距离≥0.7m，绝缘手套必须佩戴。"),
        ("human", "直接观察现场：{scene}。判断所有安全隐患。"),
    ])
    native_chain = native_prompt | llm | StrOutputParser()
    try:
        result = native_chain.invoke({"scene": scene})
        print(f"  NATIVE安全检测:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [NATIVE模式失败: {e}]")

    # EXTRACT模式
    print("\n【EXTRACT模式 - 标签提取后分析】")
    ppe_labels = "人员A=[安全帽已佩戴, 绝缘手套未佩戴, 绝缘鞋已佩戴], 人员B=[全部合规]\n围栏[3面/应4面], 距离[0.5m/要求≥0.7m]"
    extract_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是安全检测助手。基于检测标签分析安全隐患并评估。"),
        ("human", "检测标签：{labels}\n\n请给出安全评估。"),
    ])
    extract_chain = extract_prompt | llm | StrOutputParser()
    try:
        result = extract_chain.invoke({"labels": ppe_labels})
        print(f"  EXTRACT安全评估:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [EXTRACT模式失败: {e}]")

    # TOOL模式
    print("\n【TOOL模式 - Agent + 专用安全工具】")
    try:
        result = agent.invoke({
            "messages": [("user", f"请对以下场景进行安全检测：{scene}。依次调用PPE检测、距离检测和环境检测工具，然后综合给出安全评估。")]
        })
        print(f"\n  TOOL安全报告:\n  {result['messages'][-1].content[:300]}...")
    except Exception as e:
        print(f"  Agent执行出错: {e}")
        # 降级
        tool_data = f"PPE: {ppe_check(scene)}\n距离: {distance_check(scene)}\n环境: {environment_check(scene)}"
        tool_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是安全检测助手。基于安全工具返回的结构化结果生成安全检测报告并定级。"),
            ("human", "工具数据：\n{tool_data}\n\n请生成安全报告。"),
        ])
        tool_chain = tool_prompt | llm | StrOutputParser()
        try:
            result = tool_chain.invoke({"tool_data": tool_data})
            print(f"  [Chain模式] {result[:300]}...")
        except Exception as e2:
            print(f"  [Chain模式也失败: {e2}]")

    # 拓展
    print("\n--- 拓展：电力设备智能巡检 ---")
    patrol_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是电力设备巡检助手。基于巡检数据判断设备状态。"),
        ("human", "变压器巡检：外观有轻微渗油痕迹，油位计指示偏低，呼吸器硅胶变色1/3，温度计显示65℃。请判断状态。"),
    ])
    patrol_chain = patrol_prompt | llm | StrOutputParser()
    try:
        result = patrol_chain.invoke({})
        print(f"  巡检分析:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [调用失败: {e}]")

    print("\n三种模式在安全场景的对比：")
    print("  NATIVE：能发现PPE标签检测不到的问题（如手套破损、安全带未扣紧）")
    print("  EXTRACT：快速批量检测PPE佩戴，适合人员众多的场景")
    print("  TOOL：结构化违规清单可直接对接工单系统，触发整改流程")
    print("  安全推荐：TOOL做初筛 + NATIVE复核高风险场景")

    print("\n课题13完成！")


if __name__ == "__main__":
    exercise13_run()
