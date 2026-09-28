"""
Configuration module for An An Persona Chatbot.
Loads environment variables, defines paths, and manages API credentials.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Resolve project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env file
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=False)
else:
    load_dotenv(override=False)

# -----------------------------------------------------------------------------
# API Keys & Cloud Credentials
# -----------------------------------------------------------------------------
# Google Gemini API Keys (cross-fallback between GEMINI_API_KEY and GOOGLE_API_KEY)
_gemini_raw = os.getenv("GEMINI_API_KEY", "").strip()
_google_raw = os.getenv("GOOGLE_API_KEY", "").strip()

GEMINI_API_KEY: str = _gemini_raw or _google_raw
GOOGLE_API_KEY: str = _google_raw or _gemini_raw

# Ensure both environment variables are set in os.environ for third-party SDKs
if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Groq API Key
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# -----------------------------------------------------------------------------
# Data Paths
# -----------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_JSON_PATH = os.getenv(
    "FACEBOOK_JSON_PATH",
    "F:/dowload/FacebookData/messages/An An_86.json"
)

# -----------------------------------------------------------------------------
# Model & Runtime Defaults
# -----------------------------------------------------------------------------
DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "gemini").lower()
DEFAULT_MODEL_GEMINI: str = os.getenv("DEFAULT_MODEL_GEMINI", "gemini-2.0-flash")
DEFAULT_MODEL_GROQ: str = os.getenv("DEFAULT_MODEL_GROQ", "llama-3.3-70b-versatile")
DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

# -----------------------------------------------------------------------------
# Persona & Conversation Constants
# -----------------------------------------------------------------------------
PERSONA_NAME: str = "An An"
USER_NAME: str = "Hoàng Kim Quờ Lờ"
USER_NICKNAME: str = "ql"
DEFAULT_SESSION_ID: str = "default_session"

# Maximum session inactivity gap before starting a new conversation turn (2 hours in ms)
SESSION_GAP_THRESHOLD_MS: int = 7_200_000


def get_api_key(provider: str) -> Optional[str]:
    """
    Returns the API key for the specified provider.
    
    Args:
        provider: 'gemini' (or 'google') vs 'groq'.
        
    Returns:
        API key string if present, None otherwise.
    """
    p = provider.lower()
    if p in ("gemini", "google"):
        return GEMINI_API_KEY or None
    elif p == "groq":
        return GROQ_API_KEY or None
    return None


def get_active_provider() -> str:
    """
    Determines the best available LLM provider based on configured API keys.
    Returns 'gemini', 'groq', or 'mock' if no keys are available.
    """
    if DEFAULT_PROVIDER == "groq" and GROQ_API_KEY:
        return "groq"
    if GEMINI_API_KEY:
        return "gemini"
    if GROQ_API_KEY:
        return "groq"
    return "mock"


def validate_environment() -> Dict[str, Any]:
    """
    Validates key configuration settings and returns an audit dictionary.
    """
    json_path = Path(DEFAULT_JSON_PATH)
    return {
        "gemini_configured": bool(GEMINI_API_KEY),
        "groq_configured": bool(GROQ_API_KEY),
        "active_provider": get_active_provider(),
        "default_json_path": str(json_path),
        "json_path_exists": json_path.exists(),
        "project_root": str(PROJECT_ROOT),
    }
