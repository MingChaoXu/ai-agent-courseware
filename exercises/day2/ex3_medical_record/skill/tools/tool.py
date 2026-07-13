"""
基层门诊AI辅助诊疗 Skill Tool - 5 Modules
Usage:
    from tools.tool import (
        medical_generate_record, medical_interpret_lab,
        medical_recommend_treatment, medical_quality_control,
        medical_timeline_analysis, medical_health_check
    )
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

from config import Settings
from agent.agent import create_agent, analyze

VALID_MODULES = ["record", "lab", "treatment", "qc", "timeline"]


class Tool:
    def __init__(self):
        self._settings = Settings()
        self._agents = create_agent() if self._settings.is_configured() else None

    def is_ready(self) -> bool:
        return self._agents is not None

    def health_check(self) -> dict:
        return {
            "configured": self._settings.is_configured(),
            "ready": self.is_ready(),
            "modules": VALID_MODULES if self.is_ready() else [],
        }

    def initialize(self) -> dict:
        self._agents = create_agent()
        return {"status": "ok" if self._agents else "not_configured"}

    def run(self, module: str, input_text: str) -> str:
        if module not in VALID_MODULES:
            return f"[Error] Invalid module: {module}. Valid: {VALID_MODULES}"
        if not self._agents:
            self.initialize()
        if not self._agents:
            return "[Error] API not configured."
        result = analyze(self._agents, module, input_text)
        if result.get("error"):
            return result["error"]
        if isinstance(result["answer"], dict):
            return json.dumps(result["answer"], ensure_ascii=False, indent=2)
        return str(result["answer"])


_tool_instance: Optional[Tool] = None

def get_tool() -> Tool:
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = Tool()
        _tool_instance.initialize()
    return _tool_instance


def medical_generate_record(input_text: str) -> str:
    """生成规范门诊病历：从症状描述生成主诉、现病史、体检、诊断、处理意见等结构化病历。"""
    return get_tool().run("record", input_text)


def medical_interpret_lab(input_text: str) -> str:
    """解读检验报告：标注异常指标、解读临床意义、给出综合分析和复查建议。"""
    return get_tool().run("lab", input_text)


def medical_recommend_treatment(input_text: str) -> str:
    """推荐诊疗方案：根据症状推荐可能诊断、检查项目、用药方案和注意事项。"""
    return get_tool().run("treatment", input_text)


def medical_quality_control(input_text: str) -> str:
    """病历质控校验：按《病历书写基本规范》检查病历质量，评定等级并给出修改建议。"""
    return get_tool().run("qc", input_text)


def medical_timeline_analysis(input_text: str) -> str:
    """时序病情分析：根据患者多次就诊记录，分析病情演变趋势、治疗效果、风险预警，并给出后续管理建议。"""
    return get_tool().run("timeline", input_text)


def medical_health_check() -> str:
    """检查助手健康状态及可用模块。"""
    tool = get_tool()
    return json.dumps(tool.health_check(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="基层门诊AI辅助诊疗 Skill Tool")
    parser.add_argument("action", choices=["record", "lab", "treatment", "qc", "timeline", "health"], help="Module to use")
    parser.add_argument("-q", "--question", help="Input text")
    args = parser.parse_args()

    tool = Tool()
    if args.action == "health":
        print(json.dumps(tool.health_check(), ensure_ascii=False, indent=2))
    else:
        if not args.question:
            print("Please provide input with -q")
            sys.exit(1)
        if not tool.is_ready():
            tool.initialize()
        print(tool.run(args.action, args.question))
