"""
工业运维知识库 Skill Tool
"""

import os, sys, json
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
        ready = self.is_ready()
        chunks = self._agent["kb"].total_chunks if ready else 0
        return {"configured": self._settings.is_configured(), "ready": ready, "chunks": chunks}

    def initialize(self) -> dict:
        self._agent = create_agent()
        return {"status": "ok" if self._agent else "not_configured"}

    def run(self, question: str) -> str:
        if not self._agent:
            self.initialize()
        if not self._agent:
            return "[Error] API not configured."
        result = chat(self._agent, question)
        return result["answer"]


_tool_instance: Optional[Tool] = None

def get_tool() -> Tool:
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = Tool()
        _tool_instance.initialize()
    return _tool_instance

def ex2_industrial_kb_chat(question: str) -> str:
    """Ask the 工业运维知识库 a question."""
    return get_tool().run(question)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="工业运维知识库 Skill Tool")
    parser.add_argument("action", choices=["chat", "health"], help="Action")
    parser.add_argument("-q", "--question", help="Question")
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
