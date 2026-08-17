from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Use 127.0.0.1 explicitly to avoid Windows hanging on localhost IPv6 DNS resolution
    DATABASE_URL: str = "postgresql+psycopg2://jobmatch:password123@127.0.0.1:5432/jobmatch_db"
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
