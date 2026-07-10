"""
Backend Configuration
Loads from .env file, provides settings to all modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


class Settings:
    # LLM
    LLM_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_API_BASE: str = os.getenv("OPENAI_API_BASE", "")
    LLM_MODEL: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))

    # Embedding
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    EMBEDDING_API_BASE: str = os.getenv("EMBEDDING_API_BASE", os.getenv("OPENAI_API_BASE", ""))

    # RAG
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "3"))

    # Server
    HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # Data
    DATA_DIR: str = str(Path(__file__).resolve().parent.parent / "data")
    FAISS_INDEX_DIR: str = str(Path(__file__).resolve().parent / "faiss_index")

    # History
    MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "6"))

    def is_configured(self) -> bool:
        return bool(self.LLM_API_KEY and self.LLM_API_BASE)


settings = Settings()
