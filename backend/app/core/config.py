"""
core/config.py – Application settings loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "SevaSetu"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database – defaults to SQLite so no Postgres needed locally
    DATABASE_URL: str = "sqlite:///./sevasetu.db"

    # JWT
    SECRET_KEY: str = "changeme-super-secret-key-32chars!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # CORS – comma-separated origins
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # AI / RAG paths
    KNOWLEDGE_BASE_PATH: str = "./data/schemes.json"
    FAISS_INDEX_PATH: str = "./data/faiss.index"

    # Voice
    AUDIO_OUTPUT_DIR: str = "./static/audio"
    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = None

    # LLM (OpenRouter — OpenAI-compatible API)
    OPENAI_API_KEY: str | None = None
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "google/gemma-4-31b-it:free"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
