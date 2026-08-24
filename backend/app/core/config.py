from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Use 127.0.0.1 explicitly to avoid Windows hanging on localhost IPv6 DNS resolution
    DATABASE_URL: str = "postgresql+psycopg2://jobmatch:password123@127.0.0.1:5432/jobmatch_db"

    # Provider selection: "gemini", "openrouter", or "groq"
    AI_PROVIDER: str = "groq"

    # API Keys
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Models
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Security
    HTTPS_ONLY: bool = False  # Set to True in production
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
