"""
FAISS Vector Knowledge Base Manager
Handles document loading, chunking, embedding, and persistence.
"""

import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import settings


class KnowledgeBase:
    """Manages a FAISS vector store for RAG retrieval."""

    def __init__(self):
        self._embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_API_BASE,
        )
        self._vectorstore: Optional[FAISS] = None
        self._documents: Dict[str, dict] = {}  # id -> {title, chunks}
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        self._index_dir = Path(settings.FAISS_INDEX_DIR)

    @property
    def is_loaded(self) -> bool:
        return self._vectorstore is not None

    @property
    def total_chunks(self) -> int:
        if not self._vectorstore:
            return 0
        return self._vectorstore.index.ntotal

    @property
    def vectorstore(self) -> Optional[FAISS]:
        return self._vectorstore

    def list_documents(self) -> List[dict]:
        """List all uploaded documents."""
        return [
            {"id": doc_id, "title": info["title"], "chunks": info["chunks"]}
            for doc_id, info in self._documents.items()
        ]

    def upload_text(self, title: str, content: str, chunk_size: int = None) -> dict:
        """
        Upload text content to knowledge base.
        Text is split into chunks, embedded, and stored in FAISS.
        """
        if chunk_size:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=min(50, chunk_size // 10),
            )
        else:
            splitter = self._splitter

        # Split into chunks
        chunks = splitter.create_documents([content])
        doc_id = str(uuid.uuid4())[:8]

        # Add metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata = {"source": title, "chunk_index": i, "doc_id": doc_id}

        # Add to vectorstore
        if self._vectorstore is None:
            self._vectorstore = FAISS.from_documents(chunks, self._embeddings)
        else:
            self._vectorstore.add_documents(chunks)

        # Track document
        self._documents[doc_id] = {"title": title, "chunks": len(chunks)}

        return {"id": doc_id, "title": title, "chunks": len(chunks)}

    def upload_json_faq(self, filepath: str) -> dict:
        """
        Load FAQ data from a JSON file.
        Expected format: [{"category": "...", "question": "...", "answer": "..."}]
        """
        with open(filepath, "r", encoding="utf-8") as f:
            faqs = json.load(f)

        # Combine each FAQ into a single document
        combined = []
        for faq in faqs:
            text = (
                f"类别：{faq.get('category', '')}\n"
                f"问题：{faq['question']}\n"
                f"答案：{faq['answer']}"
            )
            combined.append(text)

        # Join all and upload as one document
        full_text = "\n\n---\n\n".join(combined)
        return self.upload_text(
            title=Path(filepath).stem,
            content=full_text,
        )

    def search(self, query: str, top_k: int = None) -> List[Document]:
        """Search the knowledge base for relevant documents."""
        if not self._vectorstore:
            return []
        k = top_k or settings.RETRIEVAL_TOP_K
        return self._vectorstore.similarity_search(query, k=k)

    def search_with_scores(self, query: str, top_k: int = None) -> List[tuple]:
        """Search with similarity scores."""
        if not self._vectorstore:
            return []
        k = top_k or settings.RETRIEVAL_TOP_K
        return self._vectorstore.similarity_search_with_score(query, k=k)

    def save_index(self) -> None:
        """Persist FAISS index to disk."""
        if self._vectorstore and self._index_dir:
            self._index_dir.mkdir(parents=True, exist_ok=True)
            self._vectorstore.save_local(str(self._index_dir))
            # Save metadata
            meta_path = self._index_dir / "metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(self._documents, f, ensure_ascii=False, indent=2)

    def load_index(self) -> bool:
        """Load FAISS index from disk."""
        if not self._index_dir.exists():
            return False
        try:
            self._vectorstore = FAISS.load_local(
                str(self._index_dir),
                self._embeddings,
                allow_dangerous_deserialization=True,
            )
            # Load metadata
            meta_path = self._index_dir / "metadata.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._documents = json.load(f)
            return True
        except Exception:
            return False

    def load_default_data(self) -> dict:
        """
        Load default FAQ data if no index exists.
        Returns loading stats.
        """
        if self.load_index():
            return {"status": "loaded_from_cache", "chunks": self.total_chunks}

        faq_path = os.path.join(settings.DATA_DIR, "gov_faq.json")
        if not os.path.exists(faq_path):
            return {"status": "no_data", "chunks": 0}

        result = self.upload_json_faq(faq_path)
        self.save_index()
        return {"status": "loaded_from_file", "chunks": self.total_chunks, "document": result}
