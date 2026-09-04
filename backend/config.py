import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "RecoverIQ — Risk-Adjusted Revenue Recovery Copilot"
    VERSION: str = "1.0.0"
    TRACK: str = "Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery"

    # LLM Settings
    LLM_MODE: str = os.getenv("LLM_MODE", "mock").lower()  # 'mock' or 'live'
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./recoveriq.db")

    # Fixed seed for 100% reproducible benchmark KPIs
    SIMULATION_SEED: int = int(os.getenv("SIMULATION_SEED", "42"))

    # Server settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

settings = Settings()
