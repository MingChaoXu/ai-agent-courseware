"""Configuration for Low-Altitude Agent Platform."""
import os
from pathlib import Path

# Load .env from project root or backend directory
from dotenv import load_dotenv
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
for env_path in [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
    _PROJECT_ROOT / ".env",
]:
    if env_path.exists():
        load_dotenv(str(env_path))
        break

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEST_IMAGES_DIR = DATA_DIR / "test_images"


class Settings:
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8300"))

    # Paths
    TEST_IMAGES_DIR: str = str(DATA_DIR / "test_images")
    DB_PATH: str = str(BASE_DIR / "data" / "low_altitude.db")

    # LLM
    LLM_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_API_BASE: str = os.getenv("OPENAI_API_BASE", "")
    LLM_MODEL: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))

    # CV Model
    YOLO_MODEL: str = os.getenv("YOLO_MODEL", "yolov8n.pt")
    YOLO_CONF_THRESHOLD: float = float(os.getenv("YOLO_CONF_THRESHOLD", "0.25"))
    YOLO_DEVICE: str = os.getenv("YOLO_DEVICE", "cpu")  # cpu or cuda

    # AMap (高德地图)
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")

    def is_amap_configured(self) -> bool:
        return bool(self.AMAP_API_KEY)

    @property
    def amap_mode(self) -> str:
        return "online" if self.is_amap_configured() else "offline"

    def is_configured(self) -> bool:
        return bool(self.LLM_API_KEY and self.LLM_API_BASE)

    @property
    def llm_kwargs(self) -> dict:
        return {
            "api_key": self.LLM_API_KEY,
            "base_url": self.LLM_API_BASE,
            "model": self.LLM_MODEL,
            "temperature": self.LLM_TEMPERATURE,
            "max_tokens": self.LLM_MAX_TOKENS,
        }


settings = Settings()
