"""
Comprehensive Roadshow Agent Backend - FastAPI Main Entry Point
"""

import sys
from pathlib import Path

# Add backend dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from agent import agent
from api import chat, health

# ---- App Init ----
app = FastAPI(
    title="Comprehensive Roadshow Agent",
    description="综合方案路演Agent - AI Agent Backend",
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

# ---- Initialize Agent ----
agent_instance = agent.create_agent() if settings.is_configured() else None
chat.agent_instance = agent_instance


@app.on_event("startup")
async def startup():
    """Initialize agent on startup."""
    global agent_instance
    if not settings.is_configured():
        print("[WARNING] LLM API not configured. Please set OPENAI_API_KEY and OPENAI_API_BASE in .env")
        return
    agent_instance = agent.create_agent()
    chat.agent_instance = agent_instance
    print(f"[STARTUP] Agent initialized: 综合方案路演Agent")


# ---- Register Routers ----
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# Serve frontend static files
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
serve_dir = frontend_dir / "dist" if (frontend_dir / "dist").exists() else frontend_dir
if serve_dir.exists():
    app.mount("/", StaticFiles(directory=str(serve_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
