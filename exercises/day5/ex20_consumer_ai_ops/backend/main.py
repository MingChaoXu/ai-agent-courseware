"""
Consumer AI Ops Platform - FastAPI Main Entry Point
3 modules: BI Analysis (ReAct Agent), Customer Service (RAG + Multi-Agent), Marketing (Structured Output)
"""

import sys
from pathlib import Path

# Add backend dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import check_config, HOST, PORT
from data_loader import DataLoader
from api import health, bi, cs, marketing, data

# ---- App Init ----
app = FastAPI(
    title="Consumer AI Ops Platform",
    description="消费领域AI智能运营平台 - BI分析 + 智能客服 + 精准营销",
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


@app.on_event("startup")
async def startup():
    """Initialize data on startup."""
    # Generate/load data
    DataLoader.sales()  # triggers save_all if needed
    print("[STARTUP] Data loaded successfully")

    if check_config():
        print("[STARTUP] LLM configured - all 3 modules ready (BI / CS / Marketing)")
    else:
        print("[WARNING] LLM API not configured. Please set OPENAI_API_KEY and OPENAI_API_BASE in .env")


# ---- Register Routers ----
app.include_router(health.router, prefix="/api")
app.include_router(bi.router, prefix="/api")
app.include_router(cs.router, prefix="/api")
app.include_router(marketing.router, prefix="/api")
app.include_router(data.router, prefix="/api")

# Serve frontend static files
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
serve_dir = frontend_dir / "dist" if (frontend_dir / "dist").exists() else frontend_dir
if serve_dir.exists():
    app.mount("/", StaticFiles(directory=str(serve_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
