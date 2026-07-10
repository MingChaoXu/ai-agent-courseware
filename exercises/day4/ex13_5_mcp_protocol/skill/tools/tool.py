"""
MCP工具协议演示Agent Skill Tool
Usage:
    from tools.tool import ex13_5_mcp_protocol_chat
    answer = ex13_5_mcp_protocol_chat("question")
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
from agent.agent import create_agent, chat


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

    def run(self, question: str) -> str:
        if not self._agent:
            self.initialize()
        if not self._agent:
            return "[Error] API not configured."
        result = chat(self._agent, question)
        if result.get("error"):
            return result["error"]
        return result["answer"]


_tool_instance: Optional[Tool] = None

def get_tool() -> Tool:
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = Tool()
        _tool_instance.initialize()
    return _tool_instance

def ex13_5_mcp_protocol_chat(question: str) -> str:
    """Ask the MCP工具协议演示Agent agent a question."""
    return get_tool().run(question)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MCP工具协议演示Agent Skill Tool")
    parser.add_argument("action", choices=["chat", "health"], help="Action")
    parser.add_argument("-q", "--question", help="Question to ask")
    args = parser.parse_args()

    tool = Tool()
    if args.action == "health":
        print(json.dumps(tool.health_check(), ensure_ascii=False, indent=2))
    elif args.action == "chat":
        if not args.question:
            print("Please provide a question with -q")
            sys.exit(1)
        if not tool.is_ready():
            tool.initialize()
        print(tool.run(args.question))
