"""
Traffic Incident Management Skill Tool - 5-Agent Pipeline + AMap + Incident DB
Usage:
    from tools.tool import (
        traffic_analyze, traffic_health_check,
        incident_list, incident_detail,
        amap_query_location,
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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Traffic Incident Management Skill Tool")
    parser.add_argument("action", choices=["analyze", "health", "incident-list", "incident-detail", "amap-query"],
                        help="Action to perform")
    parser.add_argument("-q", "--question", help="Input text for AI analysis")
    parser.add_argument("--incident-id", type=int, help="Incident ID")
    parser.add_argument("--keyword", help="Search keyword")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--address", help="Address for AMap query")
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
