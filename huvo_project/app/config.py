import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT_DIR / "prompts"
STATIC_DIR = ROOT_DIR / "static"
DATA_DIR = ROOT_DIR / "data"

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL", "https://api.groq.com/openai/v1"
)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-oss-120b")
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.6"))
MAX_TOOL_ROUNDS = 4
MAX_HISTORY_MESSAGES = 40


def require_api_key() -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "Set GROQ_API_KEY or OPENAI_API_KEY in your environment."
        )
    return GROQ_API_KEY
