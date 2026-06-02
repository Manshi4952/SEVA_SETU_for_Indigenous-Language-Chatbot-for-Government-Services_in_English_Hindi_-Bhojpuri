"""
core/config.py – Application settings loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "SevaSetu"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./sevasetu.db"

    SECRET_KEY: str = "changeme-super-secret-key-32chars!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    KNOWLEDGE_BASE_PATH: str = "./data/schemes_cleaned.json"
    FAISS_INDEX_PATH: str = "./data/faiss.index"

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    LLM_MODEL: str = "claude-haiku-4-5-20251001"
    LLM_MAX_TOKENS: int = 700
    LLM_TEMPERATURE: float = 0.4

    AUDIO_OUTPUT_DIR: str = "./static/audio"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
