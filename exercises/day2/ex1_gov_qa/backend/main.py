"""
Gov QA Backend - FastAPI Main Entry Point
"""

import sys
import os
from pathlib import Path

# Add backend dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from agent.knowledge_base import KnowledgeBase
from agent.rag_chain import RAGChain
from api import chat, knowledge, health

# ---- App Init ----
app = FastAPI(
    title="Gov QA Agent",
    description="Government Services QA Agent with RAG",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Initialize RAG Chain ----
kb = KnowledgeBase()
rag = RAGChain(knowledge_base=kb) if settings.is_configured() else None

# Inject into API modules
chat.rag_chain = rag
knowledge.knowledge_base = kb


@app.on_event("startup")
async def startup():
    """Load knowledge base on startup."""
    if not settings.is_configured():
        print("[WARNING] LLM API not configured. Please set OPENAI_API_KEY and OPENAI_API_BASE in .env")
        return

    result = kb.load_default_data()
    print(f"[STARTUP] Knowledge base: {result}")

    # Re-create RAG chain with loaded KB
    global rag
    rag = RAGChain(knowledge_base=kb)
    chat.rag_chain = rag
    print(f"[STARTUP] RAG chain initialized. KB has {kb.total_chunks} chunks.")


# ---- Register Routers ----
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")

# Serve frontend static files
frontend_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
