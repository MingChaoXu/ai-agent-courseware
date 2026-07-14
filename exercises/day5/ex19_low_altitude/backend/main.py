"""Low-Altitude Agent Platform - FastAPI main entry."""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from db.database import init_db, seed_if_empty
from agent.agent import create_agent
from api import chat, health, drones, orders, airspace, cv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="低空智能体协同管控平台",
    description="Multi-Agent + YOLO CV platform for low-altitude economy",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent_instance = None


@app.on_event("startup")
async def startup():
    global agent_instance
    logger.info("Initializing database...")
    init_db()
    seed_if_empty()

    logger.info("Creating agents and loading CV model...")
    agent_instance = create_agent()

    # Inject agent into API modules
    chat.agent_instance = agent_instance
    health.agent_instance = agent_instance

    logger.info(f"Platform ready. LLM configured: {settings.is_configured()}")
    logger.info(f"CV model loaded: {agent_instance['cv_service'].is_loaded}")


# Register routers
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(drones.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(airspace.router, prefix="/api")
app.include_router(cv.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "低空智能体协同管控平台",
        "version": "1.0.0",
        "docs": "/docs",
        "frontend": "/app",
    }


# Serve frontend
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
serve_dir = frontend_dir / "dist" if (frontend_dir / "dist").exists() else frontend_dir
if serve_dir.exists():
    app.mount("/app", StaticFiles(directory=str(serve_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
