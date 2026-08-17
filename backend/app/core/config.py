from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Use 127.0.0.1 explicitly to avoid Windows hanging on localhost IPv6 DNS resolution
    DATABASE_URL: str = "postgresql+psycopg2://jobmatch:password123@127.0.0.1:5432/jobmatch_db"
    GEMINI_API_KEY: str = ""
    AI_PROVIDER: str = "gemini"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
