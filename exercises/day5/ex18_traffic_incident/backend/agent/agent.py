"""
Traffic Incident Management Multi-Agent System

5-Agent pipeline with AMap API enrichment:
  1. incident_analysis_agent  - 事件感知与分类
  2. impact_assessment_agent  - 影响范围评估 (注入高德API数据)
  3. dispatch_plan_agent      - 疏导与救援方案
  4. info_publish_agent       - 多渠道信息发布
  5. review_report_agent      - 复盘报告

Execution flow:
  user input → Agent1 → [AMap enrichment] → Agent2 → Agent3 → Agent4 → Agent5
"""

import json
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings
from services.amap_client import AMapClient, POI_LABELS


def _create_llm():
    """Create LLM instance from settings."""
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )


# ============================================================
# Agent 1: Incident Analysis
# ============================================================

def incident_analysis_chain():
    """事件感知与分类Agent"""
    if not settings.is_configured():
        return None
    llm = _create_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是交通事件感知分析专家。分析用户上报的交通事件，提取以下信息：

1. **事件类型**: 交通事故/道路施工/交通拥堵/恶劣天气/设施故障/其他
2. **发生位置**: 尽量提取完整地址信息
3. **严重程度**: 轻微/一般/严重/特重大（根据涉及车辆数、伤亡情况、道路等级等判断）
4. **关键要素**: 涉及车辆数、人员伤亡、危险品、道路阻断情况等
5. **紧急程度**: 低/中/高/紧急

请按以下格式输出分析结果：
- 事件类型：xxx
- 发生位置：xxx
- 严重程度：xxx
- 关键要素：xxx
- 紧急程度：xxx
- 初步研判：xxx（简要描述事件性质和可能的影响）"""),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()


# ============================================================
# Agent 2: Impact Assessment (with AMap data injection)
# ============================================================

def impact_assessment_chain():
    """影响范围评估Agent (注入高德API实时数据)"""
    if not settings.is_configured():
        return None
    llm = _create_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是交通影响评估专家。基于事件分析结果和高德地图API返回的实时数据，评估事件影响范围。

**高德地图数据**（{amap_mode}）:
{amap_data}

请评估以下内容：
1. **影响范围**: 受影响路段、区域范围、预计影响持续时间
2. **交通影响**: 路况现状（基于API数据）、预计拥堵扩散方向、周边替代路线状况
3. **周边敏感区域**: 根据周边设施数据，评估对医院/学校/商圈等的影响
4. **救援资源**: 周边可调度的救援资源（医院、消防、交警）距离和响应时间评估
5. **风险等级**: 综合评估事件风险等级（低/中/高/极高）

请按结构化格式输出，引用高德API数据中的具体数值。"""),
        ("human", """事件分析结果：
{incident_analysis}

请评估该事件的影响范围。"""),
    ])
    return prompt | llm | StrOutputParser()


# ============================================================
# Agent 3: Dispatch Plan
# ============================================================

def dispatch_plan_chain():
    """疏导与救援方案Agent"""
    if not settings.is_configured():
        return None
    llm = _create_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是交通应急处置调度专家。基于事件分析和影响评估，制定具体的疏导与救援方案。

请输出以下方案：
1. **交通疏导方案**
   - 分流路线建议（基于高德路径规划数据）
   - 信号灯调整建议
   - 可变情报板信息内容
   - 临时管制措施

2. **救援资源调度**
   - 交警调度：派驻警力数量、岗位部署
   - 医疗救援：救护车派遣方案（基于周边医院距离）
   - 消防救援：消防车辆派遣（如涉及火灾/危险品）
   - 清障车辆：拖车/清障车调度

3. **处置时序**
   - 0-5分钟：紧急响应
   - 5-15分钟：资源到位
   - 15-30分钟：现场处置
   - 30-60分钟：恢复通行

4. **协同单位**
   - 需要通知的协同部门和联络方式"""),
        ("human", """事件分析结果：
{incident_analysis}

影响评估结果：
{impact_assessment}

高德路径规划数据：
{detour_routes}

请制定疏导与救援方案。"""),
    ])
    return prompt | llm | StrOutputParser()


# ============================================================
# Agent 4: Info Publish
# ============================================================

def info_publish_chain():
    """多渠道信息发布Agent"""
    if not settings.is_configured():
        return None
    llm = _create_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是交通信息发布专家。基于事件分析和处置方案，生成多渠道发布文案。

请为以下渠道分别生成发布文案：

1. **交通广播** (正式、简洁，适合播报)
   格式：[路况播报] 时间+地点+事件+影响+建议

2. **手机APP推送** (简洁、醒目，适合手机阅读)
   格式：标题+摘要+建议操作，控制在100字以内

3. **可变情报板** (极简，适合 roadside LED display)
   格式：≤20字，醒目提示

4. **社交媒体** (官方微博/微信，正式但亲民)
   格式：事件描述+影响范围+处置措施+安全提示

5. **内部通报** (上级管理部门)
   格式：事件编号+时间+地点+性质+处置+请求支援"""),
        ("human", """事件分析结果：
{incident_analysis}

处置方案：
{dispatch_plan}

请生成多渠道发布文案。"""),
    ])
    return prompt | llm | StrOutputParser()


# ============================================================
# Agent 5: Review Report
# ============================================================

def review_report_chain():
    """复盘报告Agent"""
    if not settings.is_configured():
        return None
    llm = _create_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是交通事件复盘分析专家。基于全流程信息，生成事件复盘报告。

请生成以下内容：

1. **事件概述**: 时间、地点、性质、严重程度
2. **处置过程回顾**: 响应时效、处置措施、资源投入
3. **处置效果评估**: 响应是否及时、方案是否合理、有无改进空间
4. **经验总结**: 成功经验、问题不足
5. **改进建议**: 流程优化、资源配置、协同机制改进
6. **风险预警**: 类似事件预防措施、预警机制建议

请以正式报告格式输出。"""),
        ("human", """事件分析：
{incident_analysis}

影响评估：
{impact_assessment}

处置方案：
{dispatch_plan}

发布文案：
{info_publish}

请生成复盘报告。"""),
    ])
    return prompt | llm | StrOutputParser()


# ============================================================
# Create Agent System
# ============================================================

def create_agent():
    """Create multi-agent system with AMap client."""
    if not settings.is_configured():
        return None
    chains = {
        "incident_analysis": incident_analysis_chain(),
        "impact_assessment": impact_assessment_chain(),
        "dispatch_plan": dispatch_plan_chain(),
        "info_publish": info_publish_chain(),
        "review_report": review_report_chain(),
    }
    amap = AMapClient()
    return {"chains": chains, "amap": amap}


# ============================================================
# Chat Pipeline (sequential with AMap enrichment)
# ============================================================

def chat(agent, question: str) -> Dict[str, Any]:
    """Run 5-agent pipeline with AMap data enrichment.

    Flow: Agent1 → [AMap query] → Agent2 → Agent3 → Agent4 → Agent5
    """
    chains = agent["chains"]
    amap = agent["amap"]
    results = {}

    # Agent 1: Incident Analysis
    try:
        r1 = chains["incident_analysis"].invoke({"input": question})
        results["incident_analysis"] = r1
    except Exception as e:
        results["incident_analysis"] = f"[分析失败] {str(e)}"
        # Still try to continue with AMap

    # Extract location from Agent1 output for AMap query
    amap_data = {}
    amap_mode = amap._mode_str()
    detour_routes_str = "无可用分流路线数据"

    # Parse location from incident analysis text
    location = _extract_location(results.get("incident_analysis", ""))
    if location:
        amap_result = amap.query_location_info(location)
        if "error" not in amap_result:
            amap_data = amap_result
            amap_mode = amap_result.get("mode", amap_mode)
            detour_routes_str = _format_detour_routes(amap_result.get("detour_routes", []))
        else:
            amap_data = {"error": amap_result.get("error", "查询失败"), "mode": amap_mode}
    else:
        amap_data = {"error": "未能从事件描述中提取位置信息", "mode": amap_mode}

    amap_data_str = json.dumps(amap_data, ensure_ascii=False, indent=2) if amap_data else "{}"

    # Agent 2: Impact Assessment (with AMap data)
    try:
        r2 = chains["impact_assessment"].invoke({
            "incident_analysis": results["incident_analysis"],
            "amap_data": amap_data_str,
            "amap_mode": amap_mode,
        })
        results["impact_assessment"] = r2
    except Exception as e:
        results["impact_assessment"] = f"[评估失败] {str(e)}"

    # Agent 3: Dispatch Plan
    try:
        r3 = chains["dispatch_plan"].invoke({
            "incident_analysis": results["incident_analysis"],
            "impact_assessment": results["impact_assessment"],
            "detour_routes": detour_routes_str,
        })
        results["dispatch_plan"] = r3
    except Exception as e:
        results["dispatch_plan"] = f"[方案生成失败] {str(e)}"

    # Agent 4: Info Publish
    try:
        r4 = chains["info_publish"].invoke({
            "incident_analysis": results["incident_analysis"],
            "dispatch_plan": results["dispatch_plan"],
        })
        results["info_publish"] = r4
    except Exception as e:
        results["info_publish"] = f"[发布文案生成失败] {str(e)}"

    # Agent 5: Review Report
    try:
        r5 = chains["review_report"].invoke({
            "incident_analysis": results["incident_analysis"],
            "impact_assessment": results["impact_assessment"],
            "dispatch_plan": results["dispatch_plan"],
            "info_publish": results["info_publish"],
        })
        results["review_report"] = r5
    except Exception as e:
        results["review_report"] = f"[复盘报告生成失败] {str(e)}"

    # AMap metadata for frontend display
    results["_amap_mode"] = amap_mode
    results["_amap_data"] = amap_data

    # Combine results for backward compatibility
    combined = "\n\n---\n\n".join([
        f"## {AGENT_LABELS[name]}\n{results[name]}"
        for name in ["incident_analysis", "impact_assessment", "dispatch_plan", "info_publish", "review_report"]
        if name in results
    ])
    return {"answer": combined, "results": results, "error": None}


# ============================================================
# Helpers
# ============================================================

AGENT_LABELS = {
    "incident_analysis": "事件感知与分类",
    "impact_assessment": "影响范围评估",
    "dispatch_plan": "疏导与救援方案",
    "info_publish": "多渠道信息发布",
    "review_report": "事件复盘报告",
}


def _extract_location(text: str) -> str:
    """Extract location from incident analysis text."""
    if not text:
        return ""
    for line in text.split("\n"):
        for label in ["发生位置", "位置", "地点", "地址"]:
            if label in line:
                # Extract after the label and colon
                parts = line.split("：")
                if len(parts) > 1:
                    loc = parts[1].strip()
                    if loc and loc != "未知" and len(loc) > 2:
                        return loc
                parts2 = line.split(":")
                if len(parts2) > 1:
                    loc = parts2[1].strip()
                    if loc and loc != "未知" and len(loc) > 2:
                        return loc
    # Fallback: look for road keywords in full text
    import re
    road_patterns = re.findall(r'[\u4e00-\u9fa5A-Za-z0-9]+(?:路|街|大道|交叉口|路口|高速|桥|隧道|辅路|段)[\u4e00-\u9fa5A-Za-z0-9]*', text)
    if road_patterns:
        return road_patterns[0]
    return ""


def _format_detour_routes(routes: list) -> str:
    """Format detour routes for LLM context."""
    if not routes:
        return "无可用分流路线数据"
    lines = []
    for i, r in enumerate(routes, 1):
        lines.append(f"路线{i}: {r.get('route', '')} | 距离: {r.get('distance', '')} | 用时: {r.get('duration', '')} | 过路费: {r.get('tolls', '')}")
    return "\n".join(lines)
