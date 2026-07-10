"""
Industrial Maintenance Knowledge Base - RAG Agent
Uses FAISS vector store + LangChain LCEL RAG chain.
"""

import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import settings


class KnowledgeBase:
    def __init__(self):
        self._embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_API_BASE,
        )
        self._vectorstore: Optional[FAISS] = None
        self._documents: Dict[str, dict] = {}
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=80,
        )
        self._index_dir = Path(settings.FAISS_INDEX_DIR)

    @property
    def is_loaded(self) -> bool:
        return self._vectorstore is not None

    @property
    def total_chunks(self) -> int:
        return self._vectorstore.index.ntotal if self._vectorstore else 0

    def list_documents(self) -> List[dict]:
        return [{"id": k, "title": v["title"], "chunks": v["chunks"]} for k, v in self._documents.items()]

    def upload_text(self, title: str, content: str, chunk_size: int = None) -> dict:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or 800,
            chunk_overlap=min(80, (chunk_size or 800) // 10),
        ) if chunk_size else self._splitter
        chunks = splitter.create_documents([content])
        doc_id = str(abs(hash(title)))[:8]
        for i, chunk in enumerate(chunks):
            chunk.metadata = {"source": title, "chunk_index": i, "doc_id": doc_id}
        if self._vectorstore is None:
            self._vectorstore = FAISS.from_documents(chunks, self._embeddings)
        else:
            self._vectorstore.add_documents(chunks)
        self._documents[doc_id] = {"title": title, "chunks": len(chunks)}
        return {"id": doc_id, "title": title, "chunks": len(chunks)}

    def upload_json_data(self, filepath: str) -> dict:
        with open(filepath, "r", encoding="utf-8") as f:
            docs = json.load(f)
        combined = []
        for doc in docs:
            text = f"标题：{doc.get('title', '')}\n{doc.get('content', '')}"
            combined.append(text)
        return self.upload_text(title=Path(filepath).stem, content="\n\n---\n\n".join(combined))

    def search(self, query: str, top_k: int = None) -> List[Document]:
        if not self._vectorstore:
            return []
        return self._vectorstore.similarity_search(query, k=top_k or settings.RETRIEVAL_TOP_K)

    def search_with_scores(self, query: str, top_k: int = None) -> List[tuple]:
        if not self._vectorstore:
            return []
        return self._vectorstore.similarity_search_with_score(query, k=top_k or settings.RETRIEVAL_TOP_K)

    def save_index(self) -> None:
        if self._vectorstore and self._index_dir:
            self._index_dir.mkdir(parents=True, exist_ok=True)
            try:
                self._vectorstore.save_local(str(self._index_dir))
            except RuntimeError:
                with tempfile.TemporaryDirectory() as tmpdir:
                    self._vectorstore.save_local(tmpdir)
                    for f in os.listdir(tmpdir):
                        shutil.copy2(os.path.join(tmpdir, f), self._index_dir / f)
            meta_path = self._index_dir / "metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(self._documents, f, ensure_ascii=False, indent=2)

    def load_index(self) -> bool:
        if not self._index_dir.exists():
            return False
        try:
            self._vectorstore = FAISS.load_local(str(self._index_dir), self._embeddings, allow_dangerous_deserialization=True)
            meta_path = self._index_dir / "metadata.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._documents = json.load(f)
            return True
        except Exception:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    for f in os.listdir(self._index_dir):
                        shutil.copy2(self._index_dir / f, os.path.join(tmpdir, f))
                    self._vectorstore = FAISS.load_local(tmpdir, self._embeddings, allow_dangerous_deserialization=True)
                    meta_path = self._index_dir / "metadata.json"
                    if meta_path.exists():
                        with open(meta_path, "r", encoding="utf-8") as f:
                            self._documents = json.load(f)
                    return True
            except Exception:
                return False

    def load_default_data(self) -> dict:
        if self.load_index():
            return {"status": "loaded_from_cache", "chunks": self.total_chunks}
        data_path = os.path.join(settings.DATA_DIR, "industrial_kb.json")
        if not os.path.exists(data_path):
            return {"status": "no_data", "chunks": 0}
        result = self.upload_json_data(data_path)
        self.save_index()
        return {"status": "loaded_from_file", "chunks": self.total_chunks, "document": result}


class ConversationMemory:
    def __init__(self, max_turns: int = 6):
        self._histories: Dict[str, list] = {}
        self._max_turns = max_turns

    def get_history(self, conv_id: str) -> list:
        return self._histories.get(conv_id, [])

    def add_message(self, conv_id: str, role: str, content: str) -> None:
        if conv_id not in self._histories:
            self._histories[conv_id] = []
        self._histories[conv_id].append({"role": role, "content": content})
        if len(self._histories[conv_id]) > self._max_turns * 2:
            self._histories[conv_id] = self._histories[conv_id][-self._max_turns * 2:]

    def clear(self, conv_id: str) -> None:
        self._histories.pop(conv_id, None)


def create_agent():
    """Create RAG agent with knowledge base."""
    if not settings.is_configured():
        return None
    kb = KnowledgeBase()
    kb.load_default_data()

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=0.2,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个工业设备运维知识助手，帮助工厂维修工程师快速查找设备故障原因和维修方案。

核心要求：
1. 严格依据参考资料回答，不编造设备参数
2. 回答格式：故障现象 → 可能原因 → 处理步骤 → 预防措施
3. 涉及安全操作的，必须标注安全警告
4. 如果问题不明确，追问设备型号和故障代码

参考资料：
{context}"""),
        ("human", "{question}"),
    ])
    memory = ConversationMemory(max_turns=settings.MAX_HISTORY_TURNS)
    return {"kb": kb, "llm": llm, "prompt": prompt, "memory": memory}


def chat(agent, question: str, conversation_id: str = None) -> Dict[str, Any]:
    """Answer question using RAG."""
    import uuid
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    kb = agent["kb"]
    raw_docs = kb.search(question)
    sources = [{"content": d.page_content[:200], "score": 0.0} for d in raw_docs]
    context = "\n\n---\n\n".join(d.page_content for d in raw_docs)

    history = agent["memory"].get_history(conversation_id)
    messages = [SystemMessage(content=agent["prompt"].messages[0].prompt.template.format(context=context))]
    for h in history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            messages.append(AIMessage(content=h["content"]))
    messages.append(HumanMessage(content=question))

    response = agent["llm"].invoke(messages)
    answer = response.content

    agent["memory"].add_message(conversation_id, "user", question)
    agent["memory"].add_message(conversation_id, "assistant", answer)

    return {"answer": answer, "sources": sources, "conversation_id": conversation_id}
