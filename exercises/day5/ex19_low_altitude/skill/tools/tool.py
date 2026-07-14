"""Skill tools for Low-Altitude Agent Platform.

Supports both CLI and import modes.
"""
import sys
import argparse
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
sys.path.insert(0, str(_BACKEND_DIR))


class LowAltitudeTool:
    """Tool wrapper for the low-altitude platform."""

    def __init__(self):
        from config import Settings
        self._settings = Settings()
        self._agents = None
        self._cv_service = None

    def is_ready(self) -> bool:
        return self._settings.is_configured()

    def initialize(self) -> dict:
        """Initialize agents and CV model."""
        from agent.agent import create_agent
        self._agents = create_agent()
        self._cv_service = self._agents.get("cv_service")
        return {
            "llm_configured": self._settings.is_configured(),
            "cv_model_loaded": self._cv_service.is_loaded if self._cv_service else False,
            "agents": ["perception", "logistics", "traffic", "emergency"],
        }

    def _ensure_agents(self):
        if self._agents is None:
            self.initialize()

    def run(self, question: str, agent: str = None) -> str:
        """Run a chat query through the multi-agent system."""
        self._ensure_agents()
        from agent.agent import chat as agent_chat
        result = agent_chat(self._agents, question, force_agent=agent)
        parts = [result.get("answer", "")]
        if result.get("cv_results"):
            cv = result["cv_results"]
            parts.append(f"\n[CV检测] 类型:{cv['detect_type']} 威胁:{cv['threat_level']} 目标:{cv['summary'].get('total', 0)}")
        parts.append(f"\n[使用Agent] {result.get('agent_used', 'unknown')}")
        return "\n".join(parts)

    def cv_detect(self, detect_type: str = "aerial", sample_name: str = None) -> str:
        """Run CV detection directly."""
        self._ensure_agents()
        from cv_service.detectors import run_detection
        cv_service = self._agents["cv_service"]
        if not cv_service.is_loaded:
            return "CV model not loaded."

        image = None
        if sample_name:
            image = cv_service.load_sample_image(sample_name)
        if image is None:
            sample_map = {
                "aerial": "urban_density", "obstacle": "construction_site",
                "intruder": "river_bridge", "landing": "open_field",
                "disaster": "construction_site", "traffic": "city_intersection",
            }
            image = cv_service.load_sample_image(sample_map.get(detect_type, "urban_density"))

        if image is None:
            return "No image available."

        result = run_detection(cv_service, image, detect_type)
        return result.analysis_text

    def status(self) -> dict:
        """Get system status."""
        from db import database as db
        db.init_db()
        db.seed_if_empty()
        drones = db.get_all_drones()
        orders = db.get_pending_orders()
        events = db.get_active_events()
        return {
            "llm_configured": self._settings.is_configured(),
            "drones": len(drones),
            "pending_orders": len(orders),
            "active_events": len(events),
            "drones_detail": [{"name": d["name"], "status": d["status"], "battery": d["battery"]} for d in drones],
        }

    def health_check(self) -> dict:
        return self.status()


_tool_instance: Optional[LowAltitudeTool] = None


def get_tool() -> LowAltitudeTool:
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = LowAltitudeTool()
    return _tool_instance


# ---- Public skill functions ----

def low_altitude_chat(question: str, agent: str = None) -> str:
    """低空智能体对话：通过自然语言与低空管控平台交互，支持空域感知、物流调度、交通管制、应急响应"""
    return get_tool().run(question, agent)


def low_altitude_cv_detect(detect_type: str = "aerial", sample_name: str = None) -> str:
    """CV视觉检测：调用YOLOv8模型进行航拍目标检测，支持aerial/obstacle/intruder/landing/disaster/traffic六种模式"""
    return get_tool().cv_detect(detect_type, sample_name)


def low_altitude_status() -> str:
    """查询低空平台状态：获取无人机编队、订单、事件等系统当前状态"""
    import json
    return json.dumps(get_tool().status(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Low-Altitude Agent Platform CLI")
    parser.add_argument("command", choices=["chat", "cv", "status"], help="Command to run")
    parser.add_argument("--question", "-q", type=str, help="Question for chat")
    parser.add_argument("--agent", "-a", type=str, default=None, help="Force agent")
    parser.add_argument("--type", "-t", type=str, default="aerial", help="CV detect type")
    parser.add_argument("--sample", "-s", type=str, default=None, help="Sample image name")

    args = parser.parse_args()

    if args.command == "chat":
        if not args.question:
            print("Error: --question is required for chat")
            sys.exit(1)
        print(get_tool().run(args.question, args.agent))
    elif args.command == "cv":
        print(get_tool().cv_detect(args.type, args.sample))
    elif args.command == "status":
        import json
        print(json.dumps(get_tool().status(), ensure_ascii=False, indent=2))
