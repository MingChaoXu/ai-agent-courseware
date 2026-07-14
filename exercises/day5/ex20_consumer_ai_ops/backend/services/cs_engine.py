"""
Customer Service Engine — RAG Knowledge Base + Multi-Agent Pipeline.
Provides intelligent Q&A, intent classification, and ticket creation.
"""

import json
import uuid
import time
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from config import get_llm, get_embeddings, check_config
from data_loader import DataLoader


# ═══════════════════════════════════════════════════════════
# RAG Knowledge Base
# ═══════════════════════════════════════════════════════════

_vectorstore = None


def _build_vectorstore():
    """Build FAISS index from FAQ data (lazy, cached)."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    faq_items = DataLoader.faq()
    docs = []
    for item in faq_items:
        text = f"问题：{item['question']}\n答案：{item['answer']}\n分类：{item['category']}"
        docs.append(Document(page_content=text, metadata={
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
        }))

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    embeddings = get_embeddings()
    _vectorstore = FAISS.from_documents(chunks, embeddings)
    return _vectorstore


def retrieve_knowledge(query: str, k: int = 3) -> list:
    """Retrieve relevant FAQ entries."""
    vs = _build_vectorstore()
    results = vs.similarity_search_with_score(query, k=k)
    sources = []
    for doc, score in results:
        sources.append({
            "content": doc.page_content,
            "category": doc.metadata.get("category", ""),
            "question": doc.metadata.get("question", ""),
            "score": round(float(score), 4),
        })
    return sources


# ═══════════════════════════════════════════════════════════
# Multi-Agent Pipeline (LCEL Chain based)
# ═══════════════════════════════════════════════════════════

# Agent 1: Intent Classification
INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是客服意图分类Agent。将用户问题分类为以下类别之一：\n"
     "订单相关 | 退换货 | 会员权益 | 配送物流 | 促销活动 | 投诉建议 | 其他\n\n"
     "输出格式：JSON {{\"intent\": \"类别\", \"confidence\": 0.0-1.0, \"keywords\": [\"关键词\"]}}"),
    ("human", "{input}"),
])

# Agent 2: FAQ Answer Generation
FAQ_ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是专业的客服回答生成Agent。根据检索到的FAQ知识，用友好专业的语气回答用户问题。\n\n"
     "要求：\n"
     "1. 基于检索到的知识回答，不要编造信息\n"
     "2. 如果检索结果不足，明确告知用户并建议转人工\n"
     "3. 回答要简洁清晰，步骤分明\n"
     "4. 语气亲切但专业\n\n"
     "检索到的相关知识：\n{context}"),
    ("human", "{question}"),
])

# Agent 3: Sentiment Assessment
SENTIMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是用户情绪评估Agent。分析用户消息的情绪倾向。\n"
     "输出：JSON {{\"emotion\": \"平静|焦躁|愤怒|感谢|失望\", \"urgency\": \"普通|加急|紧急\", \"need_escalation\": true/false}}"),
    ("human", "{input}"),
])

# Agent 4: Ticket Creation (if needed)
TICKET_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是工单生成Agent。当用户问题需要人工跟进时，生成标准工单。\n"
     "输出格式：\n"
     "工单编号: TK-XXXXX\n"
     "问题类型: ...\n"
     "优先级: 高/中/低\n"
     "问题描述: ...\n"
     "建议处理: ...\n"
     "预计处理时长: ..."),
    ("human", "用户问题: {question}\n意图分类: {intent}\n情绪评估: {sentiment}"),
])


# ═══════════════════════════════════════════════════════════
# Conversation Memory (simple in-memory dict)
# ═══════════════════════════════════════════════════════════

_conversations = {}


def _get_or_create_session(session_id: str) -> list:
    if session_id not in _conversations:
        _conversations[session_id] = []
    return _conversations[session_id]


def _add_message(session_id: str, role: str, content: str):
    _get_or_create_session(session_id).append({
        "role": role, "content": content, "timestamp": time.time()
    })


# ═══════════════════════════════════════════════════════════
# Main CS Pipeline
# ═══════════════════════════════════════════════════════════

def cs_chat(question: str, session_id: str = None) -> dict:
    """
    Full customer service pipeline:
    1. Intent classification
    2. Knowledge retrieval
    3. Answer generation
    4. Sentiment assessment
    5. Ticket creation (if needed)
    """
    if not check_config():
        return {"error": "LLM未配置"}

    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    llm = get_llm(temperature=0.2)

    # Step 1: Intent Classification
    intent_chain = INTENT_PROMPT | llm | StrOutputParser()
    try:
        intent_raw = intent_chain.invoke({"input": question})
        # Try to parse JSON
        import re
        json_match = re.search(r'\{[^}]+\}', intent_raw)
        intent_data = json.loads(json_match.group()) if json_match else {"intent": "其他", "confidence": 0.5}
    except Exception:
        intent_data = {"intent": "其他", "confidence": 0.5}

    # Step 2: Knowledge Retrieval
    sources = retrieve_knowledge(question, k=3)
    context = "\n\n".join([s["content"] for s in sources])

    # Step 3: Answer Generation
    answer_chain = FAQ_ANSWER_PROMPT | llm | StrOutputParser()
    try:
        answer = answer_chain.invoke({"context": context, "question": question})
    except Exception as e:
        answer = f"抱歉，系统暂时无法回答。请稍后再试或联系人工客服。（错误：{e}）"

    # Step 4: Sentiment Assessment
    sentiment_chain = SENTIMENT_PROMPT | llm | StrOutputParser()
    try:
        sentiment_raw = sentiment_chain.invoke({"input": question})
        json_match = re.search(r'\{[^}]+\}', sentiment_raw)
        sentiment_data = json.loads(json_match.group()) if json_match else {"emotion": "平静", "urgency": "普通", "need_escalation": False}
    except Exception:
        sentiment_data = {"emotion": "平静", "urgency": "普通", "need_escalation": False}

    # Step 5: Ticket Creation (if urgency or escalation needed)
    ticket = None
    if sentiment_data.get("need_escalation") or sentiment_data.get("urgency") in ["加急", "紧急"]:
        ticket_chain = TICKET_PROMPT | llm | StrOutputParser()
        try:
            ticket = ticket_chain.invoke({
                "question": question,
                "intent": intent_data.get("intent", "其他"),
                "sentiment": json.dumps(sentiment_data, ensure_ascii=False),
            })
        except Exception:
            ticket = "工单生成失败"

    # Save to conversation memory
    _add_message(session_id, "user", question)
    _add_message(session_id, "assistant", answer)

    return {
        "answer": answer,
        "intent": intent_data,
        "sources": sources,
        "sentiment": sentiment_data,
        "ticket": ticket,
        "session_id": session_id,
    }


def get_conversation_history(session_id: str) -> list:
    return _conversations.get(session_id, [])


def get_faq_suggestions(category: str = None) -> list:
    """Get FAQ suggestions, optionally filtered by category."""
    faq = DataLoader.faq()
    if category:
        faq = [f for f in faq if f["category"] == category]
    return faq[:10]
