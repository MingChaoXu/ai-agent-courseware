"""
Configuration & LLM utilities for Consumer AI Ops Platform.
Reads .env from exercise root and provides get_llm / get_embeddings helpers.
"""

import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Load .env from exercise root
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH, override=True)

# Suppress langchain-community deprecation
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_community")

# LLM config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Embedding config (may differ from LLM)
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY") or OPENAI_API_KEY
EMBEDDING_API_BASE = os.getenv("EMBEDDING_API_BASE") or OPENAI_API_BASE
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002")

# Data directory (JSON cache)
DATA_DIR = Path(__file__).parent / "data"

# Server
HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", "8000"))


def check_config() -> bool:
    """Return True if LLM is configured."""
    return bool(OPENAI_API_KEY and OPENAI_API_KEY != "sk-your-api-key-here")


def get_llm(**kwargs):
    """Create a ChatOpenAI instance."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=OPENAI_MODEL_NAME,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        temperature=kwargs.get("temperature", 0.3),
        max_tokens=kwargs.get("max_tokens", 4096),
    )


def get_embeddings():
    """Create an OpenAIEmbeddings instance (may use separate API)."""
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        openai_api_key=EMBEDDING_API_KEY,
        openai_api_base=EMBEDDING_API_BASE,
    )
