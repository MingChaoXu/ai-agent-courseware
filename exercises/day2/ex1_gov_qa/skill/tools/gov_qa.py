"""
政务问答技能工具 — 可注册为 TeleAgent 技能工具

用法:
    from tools.gov_qa import GovQATool

    tool = GovQATool()
    tool.initialize()
    answer = tool.run("新生儿落户需要什么材料？")

命令行:
    python skill/tools/gov_qa.py init
    python skill/tools/gov_qa.py answer -q "公积金贷款最高额度是多少？"
    python skill/tools/gov_qa.py search -q "居住证"
    python skill/tools/gov_qa.py list
    python skill/tools/gov_qa.py upload-file -f data/test_居住证申领指南.md
    python skill/tools/gov_qa.py clear -c conv_123
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# 项目根目录: ex1_gov_qa/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 将 backend 目录加入导入路径
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv

# 从项目根目录加载 .env
load_dotenv(_PROJECT_ROOT / ".env")

from config import Settings
from agent.knowledge_base import KnowledgeBase
from agent.rag_chain import RAGChain


class GovQATool:
    """
    政务服务问答工具。
    封装 RAG 链，可作为 TeleAgent 技能工具使用。
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or Settings()
        self._kb = KnowledgeBase()
        self._chain: Optional[RAGChain] = None

        if self._settings.is_configured():
            self._chain = RAGChain(knowledge_base=self._kb)

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        """检查工具是否已配置且知识库已加载。"""
        return self._chain is not None and self._kb.is_loaded

    def health_check(self) -> dict:
        """
        返回工具健康状态。

        返回:
            {
                "configured": bool,
                "kb_loaded": bool,
                "total_chunks": int,
                "documents": int,
            }
        """
        return {
            "configured": self._settings.is_configured(),
            "kb_loaded": self._kb.is_loaded,
            "total_chunks": self._kb.total_chunks,
            "documents": len(self._kb.list_documents()),
        }

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def initialize(self) -> dict:
        """
        加载默认知识库数据。首次使用前必须调用。
        """
        result = self._kb.load_default_data()
        if self._settings.is_configured():
            self._chain = RAGChain(knowledge_base=self._kb)
        return result

    # ------------------------------------------------------------------
    # 问答
    # ------------------------------------------------------------------

    def run(self, question: str, conversation_id: Optional[str] = None) -> str:
        """
        使用 RAG 回答政务问题，仅返回回答文本。

        Args:
            question: 用户问题
            conversation_id: 可选，多轮对话 ID

        Returns:
            回答字符串
        """
        result = self.answer_with_sources(question, conversation_id)
        return result["answer"]

    def answer_with_sources(
        self, question: str, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 RAG 回答政务问题，返回完整结果（含参考来源）。

        Args:
            question: 用户问题
            conversation_id: 可选，多轮对话 ID

        Returns:
            {
                "answer": str,
                "sources": [{"content": str, "score": float}],
                "conversation_id": str,
            }
        """
        if not self._chain:
            return {
                "answer": "[错误] 工具未配置，请设置 OPENAI_API_KEY 和 OPENAI_API_BASE。",
                "sources": [],
                "conversation_id": "",
            }

        if not self._kb.is_loaded:
            self.initialize()

        return self._chain.chat(question=question, conversation_id=conversation_id)

    # ------------------------------------------------------------------
    # 知识库管理
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5) -> str:
        """
        搜索知识库，返回相关文档（JSON 字符串）。

        Args:
            query: 搜索关键词
            top_k: 返回条数

        Returns:
            JSON 字符串，包含 content 和 score
        """
        if not self._kb.is_loaded:
            self.initialize()

        results = self._kb.search_with_scores(query, top_k=top_k)
        output = [
            {
                "content": doc.page_content[:500],
                "score": round(float(score), 4),
                "source": doc.metadata.get("source", ""),
            }
            for doc, score in results
        ]
        return json.dumps(output, ensure_ascii=False, indent=2)

    def upload(self, title: str, content: str) -> str:
        """
        上传文本内容到知识库。

        Args:
            title: 文档标题
            content: 文档文本内容

        Returns:
            上传结果消息
        """
        if not self._kb.is_loaded:
            self.initialize()

        result = self._kb.upload_text(title=title, content=content)
        self._kb.save_index()
        return f"已上传文档 '{result['title']}'，共 {result['chunks']} 个知识块。"

    def upload_file(self, file_path: str) -> str:
        """
        上传文件到知识库，支持 .txt / .md / .json（FAQ格式）。

        Args:
            file_path: 文件路径

        Returns:
            上传结果消息
        """
        if not self._kb.is_loaded:
            self.initialize()

        path = Path(file_path)
        if not path.exists():
            return f"[错误] 文件不存在: {file_path}"

        suffix = path.suffix.lower()
        if suffix == ".json":
            result = self._kb.upload_json_faq(str(path))
        elif suffix in (".txt", ".md"):
            content = path.read_text(encoding="utf-8")
            result = self._kb.upload_text(title=path.name, content=content)
        else:
            return f"[错误] 不支持的文件格式: {suffix}（仅支持 .txt / .md / .json）"

        self._kb.save_index()
        return f"已上传文件 '{result['title']}'，共 {result['chunks']} 个知识块。"

    def list_documents(self) -> str:
        """
        列出知识库中所有文档。

        Returns:
            JSON 字符串，包含文档列表和总知识块数
        """
        if not self._kb.is_loaded:
            self.initialize()

        docs = self._kb.list_documents()
        output = {
            "total_chunks": self._kb.total_chunks,
            "documents": docs,
        }
        return json.dumps(output, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 对话管理
    # ------------------------------------------------------------------

    def clear_conversation(self, conversation_id: str) -> str:
        """
        清除指定对话的历史记录。

        Args:
            conversation_id: 对话 ID

        Returns:
            操作结果消息
        """
        if self._chain:
            self._chain.clear_conversation(conversation_id)
            return f"已清除对话 {conversation_id} 的历史记录。"
        return "[错误] 工具未初始化。"


# ======================================================================
# TeleAgent 技能工具注册接口
# ======================================================================

_tool_instance: Optional[GovQATool] = None


def get_tool() -> GovQATool:
    """获取或创建全局工具实例。"""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = GovQATool()
        _tool_instance.initialize()
    return _tool_instance


def gov_qa_answer(question: str, conversation_id: str = None) -> str:
    """根据政务知识库回答问题。"""
    return get_tool().run(question, conversation_id)


def gov_qa_search(query: str, top_k: int = 5) -> str:
    """搜索政务知识库中的相关文档。"""
    return get_tool().search(query, top_k)


def gov_qa_upload(title: str, content: str) -> str:
    """上传文本到政务知识库。"""
    return get_tool().upload(title, content)


def gov_qa_upload_file(file_path: str) -> str:
    """上传文件到政务知识库（支持 .txt/.md/.json）。"""
    return get_tool().upload_file(file_path)


def gov_qa_list() -> str:
    """列出知识库中的所有文档。"""
    return get_tool().list_documents()


def gov_qa_clear(conversation_id: str) -> str:
    """清除指定对话的历史记录。"""
    return get_tool().clear_conversation(conversation_id)


# ======================================================================
# 命令行测试入口
# ======================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="政务服务问答技能工具")
    parser.add_argument(
        "action",
        choices=["init", "answer", "search", "upload", "upload-file", "list", "clear", "health"],
        help="操作类型",
    )
    parser.add_argument("-q", "--question", help="要提问的问题")
    parser.add_argument("--query", help="搜索关键词")
    parser.add_argument("--title", help="上传文档标题")
    parser.add_argument("--content", help="上传文档内容")
    parser.add_argument("-f", "--file", help="上传文件路径")
    parser.add_argument("-c", "--conv", help="对话ID")
    parser.add_argument("--top-k", type=int, default=5, help="搜索返回条数")
    args = parser.parse_args()

    tool = GovQATool()

    if args.action == "init":
        result = tool.initialize()
        print(f"初始化结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    elif args.action == "health":
        result = tool.health_check()
        print(f"健康状态: {json.dumps(result, ensure_ascii=False, indent=2)}")

    elif args.action == "answer":
        if not args.question:
            print("请使用 -q 提供问题")
            sys.exit(1)
        if not tool.is_ready():
            tool.initialize()
        result = tool.answer_with_sources(args.question, args.conv)
        print(f"\n回答:\n{result['answer']}")
        if result["sources"]:
            print(f"\n参考来源 ({len(result['sources'])} 条):")
            for i, src in enumerate(result["sources"], 1):
                print(f"  [{i}] {src['content'][:100]}...")
        if result["conversation_id"]:
            print(f"\n对话ID: {result['conversation_id']}")

    elif args.action == "search":
        if not args.query:
            print("请使用 --query 提供搜索关键词")
            sys.exit(1)
        if not tool.is_ready():
            tool.initialize()
        print(tool.search(args.query, args.top_k))

    elif args.action == "upload":
        if not args.title or not args.content:
            print("请使用 --title 和 --content 提供上传内容")
            sys.exit(1)
        print(tool.upload(args.title, args.content))

    elif args.action == "upload-file":
        if not args.file:
            print("请使用 -f 提供文件路径")
            sys.exit(1)
        print(tool.upload_file(args.file))

    elif args.action == "list":
        print(tool.list_documents())

    elif args.action == "clear":
        if not args.conv:
            print("请使用 -c 提供对话ID")
            sys.exit(1)
        print(tool.clear_conversation(args.conv))
