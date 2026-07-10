"""
Gov QA Skill Tools - Can be registered as TeleAgent tools

Usage:
    from tools.gov_qa import GovQATool

    tool = GovQATool()
    answer = tool.run("新生儿落户需要什么材料？")
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

# Ensure backend is importable
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

from config import Settings
from agent.knowledge_base import KnowledgeBase
from agent.rag_chain import RAGChain


class GovQATool:
    """
    Government Services QA Tool.
    Wraps the RAG chain for use as a TeleAgent skill tool.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or Settings()
        self._kb = KnowledgeBase()
        self._chain: Optional[RAGChain] = None

        if self._settings.is_configured():
            self._chain = RAGChain(knowledge_base=self._kb)

    def is_ready(self) -> bool:
        """Check if the tool is properly configured and ready."""
        return self._chain is not None and self._kb.is_loaded

    def initialize(self) -> dict:
        """
        Initialize the tool by loading default knowledge base data.
        Call this before using the tool for the first time.
        """
        result = self._kb.load_default_data()
        # Re-create chain after loading KB
        if self._settings.is_configured():
            self._chain = RAGChain(knowledge_base=self._kb)
        return result

    def run(self, question: str, conversation_id: Optional[str] = None) -> str:
        """
        Answer a government service question using RAG.

        Args:
            question: The citizen's question
            conversation_id: Optional conversation ID for multi-turn chat

        Returns:
            The answer string
        """
        if not self._chain:
            return "[Error] Tool not configured. Please set OPENAI_API_KEY and OPENAI_API_BASE."

        if not self._kb.is_loaded:
            self.initialize()

        result = self._chain.chat(question=question, conversation_id=conversation_id)
        return result["answer"]

    def search(self, query: str, top_k: int = 5) -> str:
        """
        Search the knowledge base for relevant documents.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            JSON string of search results
        """
        if not self._kb.is_loaded:
            self.initialize()

        results = self._kb.search(query, top_k=top_k)
        output = [{"content": doc.page_content, "source": doc.metadata.get("source", "")} for doc in results]
        return json.dumps(output, ensure_ascii=False, indent=2)

    def upload(self, title: str, content: str) -> str:
        """
        Upload new text content to the knowledge base.

        Args:
            title: Document title
            content: Document text content

        Returns:
            Upload result message
        """
        result = self._kb.upload_text(title=title, content=content)
        self._kb.save_index()
        return f"Uploaded '{result['title']}' with {result['chunks']} chunks."


# ---- Tool Registration Interface ----
# These functions match the TeleAgent skill tool contract

_tool_instance: Optional[GovQATool] = None


def get_tool() -> GovQATool:
    """Get or create the global tool instance."""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = GovQATool()
        _tool_instance.initialize()
    return _tool_instance


def gov_qa_answer(question: str, conversation_id: str = None) -> str:
    """Answer a government service question using RAG knowledge base."""
    return get_tool().run(question, conversation_id)


def gov_qa_search(query: str, top_k: int = 5) -> str:
    """Search the government services knowledge base for relevant documents."""
    return get_tool().search(query, top_k)


def gov_qa_upload(title: str, content: str) -> str:
    """Upload new documents to the government services knowledge base."""
    return get_tool().upload(title, content)


# ---- CLI for testing ----
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gov QA Skill Tool")
    parser.add_argument("action", choices=["answer", "search", "upload", "init"])
    parser.add_argument("--question", "-q", help="Question to ask")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--title", help="Upload title")
    parser.add_argument("--content", help="Upload content")
    args = parser.parse_args()

    tool = GovQATool()

    if args.action == "init":
        result = tool.initialize()
        print(f"Initialization result: {result}")
    elif args.action == "answer":
        if not args.question:
            print("Please provide --question")
            sys.exit(1)
        if not tool.is_ready():
            tool.initialize()
        print(tool.run(args.question))
    elif args.action == "search":
        if not args.query:
            print("Please provide --query")
            sys.exit(1)
        if not tool.is_ready():
            tool.initialize()
        print(tool.search(args.query))
    elif args.action == "upload":
        if not args.title or not args.content:
            print("Please provide --title and --content")
            sys.exit(1)
        print(tool.upload(args.title, args.content))
