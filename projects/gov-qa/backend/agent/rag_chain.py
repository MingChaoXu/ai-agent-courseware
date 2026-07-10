"""
RAG Chain - LangChain LCEL implementation for Gov QA
"""

from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document

from config import settings
from agent.prompts import get_rag_prompt
from agent.knowledge_base import KnowledgeBase


class ConversationMemory:
    """Simple in-memory conversation history manager."""

    def __init__(self, max_turns: int = 6):
        self._histories: Dict[str, List[BaseMessage]] = {}
        self._max_turns = max_turns

    def get_history(self, conversation_id: str) -> List[BaseMessage]:
        return self._histories.get(conversation_id, [])

    def add_message(self, conversation_id: str, message: BaseMessage) -> None:
        if conversation_id not in self._histories:
            self._histories[conversation_id] = []
        self._histories[conversation_id].append(message)
        # Trim to max turns
        if len(self._histories[conversation_id]) > self._max_turns:
            self._histories[conversation_id] = self._histories[conversation_id][-self._max_turns:]

    def clear(self, conversation_id: str) -> None:
        self._histories.pop(conversation_id, None)


class RAGChain:
    """
    RAG Chain for Government QA.

    Flow: User Question → Retriever → Prompt(with context+history) → LLM → Parser → Answer
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        self._kb = knowledge_base
        self._llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_BASE,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        self._prompt = get_rag_prompt()
        self._memory = ConversationMemory(max_turns=settings.MAX_HISTORY_TURNS)
        self._chain = self._build_chain()

    def _format_docs(self, docs: List[Document]) -> str:
        """Format retrieved documents into a single string."""
        return "\n\n---\n\n".join(d.page_content for d in docs)

    def _build_chain(self):
        """Build the LCEL RAG chain."""
        return (
            {
                "context": RunnableLambda(self._retrieve) | RunnableLambda(self._format_docs),
                "question": RunnablePassthrough(),
                "history": RunnableLambda(self._get_history),
            }
            | self._prompt
            | self._llm
            | StrOutputParser()
        )

    def _retrieve(self, question: str) -> List[Document]:
        """Retrieve relevant documents from knowledge base."""
        return self._kb.search(question)

    def _get_history(self, _input) -> List[BaseMessage]:
        """Get conversation history for current conversation."""
        # History is passed separately, this is a placeholder
        return []

    def chat(
        self,
        question: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Chat with the RAG agent.

        Returns:
            {
                "answer": str,
                "sources": [{"content": str, "score": float}],
                "conversation_id": str,
            }
        """
        if not conversation_id:
            conversation_id = f"conv_{id(question)}"

        # Retrieve documents first (for source attribution)
        raw_docs = self._kb.search(question)
        sources = [
            {"content": doc.page_content[:200], "score": 0.0}
            for doc in raw_docs
        ]

        # Build messages manually for history support
        from langchain_core.messages import SystemMessage

        context_str = self._format_docs(raw_docs)
        history = self._memory.get_history(conversation_id)

        messages = [
            SystemMessage(content=self._prompt.messages[0].prompt.template.format(context=context_str)),
        ]
        messages.extend(history)
        messages.append(HumanMessage(content=question))

        # Invoke LLM
        response = self._llm.invoke(messages)
        answer = response.content

        # Update memory
        self._memory.add_message(conversation_id, HumanMessage(content=question))
        self._memory.add_message(conversation_id, AIMessage(content=answer))

        return {
            "answer": answer,
            "sources": sources,
            "conversation_id": conversation_id,
        }

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation history."""
        self._memory.clear(conversation_id)
