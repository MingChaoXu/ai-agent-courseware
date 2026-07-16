"""
Traffic Incident Management Backend - FastAPI Main Entry Point
5-Agent pipeline + AMap API + Incident database
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
from api import chat, health, incidents, police
from db.database import init_db, seed_if_empty

# ---- App Init ----
app = FastAPI(
    title="Traffic Incident Management Agent",
    description="交通事件智能处置Agent - 5Agent协作 + 高德地图API",
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
    """Initialize agent and database on startup."""
    global agent_instance

    # Initialize database
    init_db()
    seed_if_empty()
    print("[STARTUP] Database initialized with seed data")

    # Initialize agent
    if not settings.is_configured():
        print("[WARNING] LLM API not configured. Please set OPENAI_API_KEY and OPENAI_API_BASE in .env")
        return
    agent_instance = agent.create_agent()
    chat.agent_instance = agent_instance
    amap_status = "高德API在线模式" if settings.is_amap_configured() else "高德API离线模式（模拟数据）"
    print(f"[STARTUP] Agent initialized: 交通事件智能处置Agent")
    print(f"[STARTUP] AMap mode: {amap_status}")


# ---- Register Routers ----
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")
app.include_router(police.router, prefix="/api")

# Serve frontend static files
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
serve_dir = frontend_dir / "dist" if (frontend_dir / "dist").exists() else frontend_dir
if serve_dir.exists():
    app.mount("/", StaticFiles(directory=str(serve_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
