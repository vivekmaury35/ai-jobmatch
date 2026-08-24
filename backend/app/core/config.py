from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://jobmatch:password123@127.0.0.1:5432/jobmatch_db"

    # Provider selection: "openrouter", "gemini", or "groq"
    AI_PROVIDER: str = "openrouter"

    # API Keys (read from environment / .env)
    OPENROUTER_API_KEY: Optional[str] = None
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: Optional[str] = None

    # Models - Default to cheap, fast, high-performance gpt-4o-mini ($0.15/1M tokens)
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Security
    HTTPS_ONLY: bool = False
    ENVIRONMENT: str = "production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
