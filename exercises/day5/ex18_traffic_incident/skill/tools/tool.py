"""
Traffic Incident Management Skill Tool - 5-Agent Pipeline + AMap + Incident DB + Police Force
Usage:
    from tools.tool import (
        traffic_analyze, traffic_health_check,
        incident_list, incident_detail,
        amap_query_location,
        police_units, police_allocate,
        police_personnel, police_personnel_stats,
    )
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

from config import Settings
from agent.agent import create_agent, chat as agent_chat
from services.amap_client import AMapClient


class Tool:
    def __init__(self):
        self._settings = Settings()
        self._agents = create_agent() if self._settings.is_configured() else None
        self._amap = AMapClient()

    def is_ready(self) -> bool:
        return self._agents is not None

    def health_check(self) -> dict:
        return {
            "configured": self._settings.is_configured(),
            "ready": self.is_ready(),
            "amap_mode": self._settings.amap_mode,
            "modules": ["incident_analysis", "impact_assessment", "dispatch_plan", "info_publish", "review_report"] if self.is_ready() else [],
        }

    def initialize(self) -> dict:
        self._agents = create_agent()
        return {"status": "ok" if self._agents else "not_configured"}

    def run_analyze(self, input_text: str) -> str:
        if not self._agents:
            self.initialize()
        if not self._agents:
            return "[Error] LLM API not configured."
        result = agent_chat(self._agents, input_text)
        if result.get("error"):
            return result["error"]
        # Return structured results
        results = result.get("results", {})
        amap_mode = results.pop("_amap_mode", "")
        amap_data = results.pop("_amap_data", {})
        output = f"=== 高德地图模式: {amap_mode} ===\n\n"
        for key in ["incident_analysis", "impact_assessment", "dispatch_plan", "info_publish", "review_report"]:
            if key in results:
                labels = {
                    "incident_analysis": "事件感知与分类",
                    "impact_assessment": "影响范围评估",
                    "dispatch_plan": "疏导与救援方案",
                    "info_publish": "多渠道信息发布",
                    "review_report": "事件复盘报告",
                }
                output += f"--- {labels.get(key, key)} ---\n{results[key]}\n\n"
        return output

    def run_amap_query(self, address: str) -> str:
        result = self._amap.query_location_info(address)
        return json.dumps(result, ensure_ascii=False, indent=2)


_tool_instance: Optional[Tool] = None


def get_tool() -> Tool:
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = Tool()
        _tool_instance.initialize()
    return _tool_instance


# ============================================================
# AI Analysis Modules
# ============================================================

def traffic_analyze(input_text: str) -> str:
    """交通事件智能处置：输入事件描述，5个Agent协作完成事件感知→影响评估→疏导方案→信息发布→复盘报告。"""
    return get_tool().run_analyze(input_text)


def traffic_health_check() -> str:
    """检查Agent健康状态、高德API模式及可用模块。"""
    tool = get_tool()
    return json.dumps(tool.health_check(), ensure_ascii=False, indent=2)


# ============================================================
# Incident Database Tools
# ============================================================

def incident_list(keyword: str = "", status: str = "") -> str:
    """查询交通事件列表，可按关键词和状态筛选。返回事件ID、描述、类型、位置、严重程度、状态等信息。"""
    from db.database import list_incidents
    result = list_incidents(keyword, status)
    return json.dumps(result, ensure_ascii=False, indent=2)


def incident_detail(incident_id: int) -> str:
    """获取事件完整详情：基本信息、AI分析摘要、处置记录（含疏导方案、发布文案、复盘报告）。"""
    from db.database import get_incident, get_dispatches
    incident = get_incident(incident_id)
    if not incident:
        return f"[Error] Incident {incident_id} not found"
    dispatches = get_dispatches(incident_id)
    out = {
        "incident": incident,
        "dispatches": dispatches,
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


# ============================================================
# AMap Query Tools
# ============================================================

def amap_query_location(address: str) -> str:
    """查询地理位置信息：地理编码（地址→经纬度）、周边设施（医院/消防/交警/加油站）、实时路况、分流路线。
    在线模式调用高德实时API，离线模式返回模拟数据。"""
    return get_tool().run_amap_query(address)


# ============================================================
# Police Force Tools
# ============================================================

def police_units() -> str:
    """获取所有警力单位信息：单位名称、类型（交警/巡警/特警/派出所）、位置、人数、状态、联系方式。
    数据模拟来自警务指挥系统实时接口。"""
    from services.police_service import get_all_units
    units = get_all_units()
    return json.dumps({"units": units, "total": len(units)}, ensure_ascii=False, indent=2)


def police_allocate(lng: float, lat: float, severity: str = "一般") -> str:
    """根据事故位置和严重程度，计算最优警力调配方案。

    算法综合考虑直线距离、可用人数、单位类型覆盖和预计到达时间。
    不同严重程度对应不同配置：
    - 轻微: 3人, 1单位, 交警
    - 一般: 6人, 2单位, 交警
    - 严重: 12人, 3单位, 交警+巡警
    - 特重大: 20人, 4单位, 交警+特警+巡警

    Args:
        lng: 事故经度 (GCJ-02坐标系)
        lat: 事故纬度 (GCJ-02坐标系)
        severity: 严重程度，可选值: 轻微/一般/严重/特重大
    """
    from services.police_service import allocate_police
    result = allocate_police(incident_lng=lng, incident_lat=lat, incident_severity=severity)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# Personnel Database Tools
# ============================================================

def police_personnel(keyword: str = "", unit_type: str = "", status: str = "", role: str = "") -> str:
    """搜索警力人员数据库（OA系统）：支持按姓名/警号/单位/电话/技能搜索，按单位类型/状态/岗位筛选。
    返回人员详细信息包括警衔、岗位、联系方式、技能特长、资质证书等。"""
    from services.police_service import search_personnel
    results = search_personnel(
        keyword=keyword or None,
        unit_type=unit_type or None,
        status=status or None,
        role=role or None,
    )
    return json.dumps({"personnel": results, "total": len(results)}, ensure_ascii=False, indent=2)


def police_personnel_stats() -> str:
    """获取警力人员统计摘要：总人数、按单位类型分布（交警/巡警/特警/派出所）、按状态分布（待命/执勤/休假）、按岗位分布。"""
    from services.police_service import get_personnel_stats
    result = get_personnel_stats()
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Traffic Incident Management Skill Tool")
    parser.add_argument("action", choices=[
        "analyze", "health",
        "incident-list", "incident-detail",
        "amap-query",
        "police-units", "police-allocate",
        "police-personnel", "police-personnel-stats",
    ], help="Action to perform")
    parser.add_argument("-q", "--question", help="Input text for AI analysis")
    parser.add_argument("--incident-id", type=int, help="Incident ID")
    parser.add_argument("--keyword", help="Search keyword")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--address", help="Address for AMap query")
    parser.add_argument("--lng", type=float, help="Longitude for police allocation (GCJ-02)")
    parser.add_argument("--lat", type=float, help="Latitude for police allocation (GCJ-02)")
    parser.add_argument("--severity", default="一般", help="Severity for police allocation: 轻微/一般/严重/特重大")
    parser.add_argument("--unit-type", help="Filter by unit type: 交警/巡警/特警/派出所")
    parser.add_argument("--role", help="Filter by role: 指挥员/巡逻员/...")
    args = parser.parse_args()

    if args.action == "health":
        tool = Tool()
        print(json.dumps(tool.health_check(), ensure_ascii=False, indent=2))
    elif args.action == "analyze":
        if not args.question:
            print("Please provide input with -q"); sys.exit(1)
        tool = Tool()
        if not tool.is_ready(): tool.initialize()
        print(tool.run_analyze(args.question))
    elif args.action == "incident-list":
        print(incident_list(args.keyword or "", args.status or ""))
    elif args.action == "incident-detail":
        if not args.incident_id:
            print("Please provide --incident-id"); sys.exit(1)
        print(incident_detail(args.incident_id))
    elif args.action == "amap-query":
        if not args.address:
            print("Please provide --address"); sys.exit(1)
        print(amap_query_location(args.address))
    elif args.action == "police-units":
        print(police_units())
    elif args.action == "police-allocate":
        if args.lng is None or args.lat is None:
            print("Please provide --lng and --lat"); sys.exit(1)
        print(police_allocate(args.lng, args.lat, args.severity))
    elif args.action == "police-personnel":
        print(police_personnel(
            keyword=args.keyword or "",
            unit_type=args.unit_type or "",
            status=args.status or "",
            role=args.role or "",
        ))
    elif args.action == "police-personnel-stats":
        print(police_personnel_stats())
