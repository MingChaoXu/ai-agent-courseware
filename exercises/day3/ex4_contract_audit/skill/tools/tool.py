"""
合同风险智能审查 Skill Tool
Usage:
    from tools.tool import ex4_contract_audit_analyze
    result = ex4_contract_audit_analyze("input text")
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


class Tool:
    def __init__(self):
        self._settings = Settings()
        self._agent = create_agent() if self._settings.is_configured() else None

    def is_ready(self) -> bool:
        return self._agent is not None

    def health_check(self) -> dict:
        return {"configured": self._settings.is_configured(), "ready": self.is_ready()}

    def initialize(self) -> dict:
        self._agent = create_agent()
        return {"status": "ok" if self._agent else "not_configured"}

    def run(self, input_text: str) -> str:
        if not self._agent:
            self.initialize()
        if not self._agent:
            return "[Error] API not configured."
        result = analyze(self._agent, input_text)
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

def ex4_contract_audit_analyze(input_text: str) -> str:
    """Analyze input text and return structured result."""
    return get_tool().run(input_text)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="合同风险智能审查 Skill Tool")
    parser.add_argument("action", choices=["analyze", "health"], help="Action")
    parser.add_argument("-q", "--question", help="Input text to analyze")
    args = parser.parse_args()

    tool = Tool()
    if args.action == "health":
        print(json.dumps(tool.health_check(), ensure_ascii=False, indent=2))
    elif args.action == "analyze":
        if not args.question:
            print("Please provide input with -q")
            sys.exit(1)
        if not tool.is_ready():
            tool.initialize()
        print(tool.run(args.question))
