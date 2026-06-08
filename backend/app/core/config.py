"""
core/config.py – Application settings loaded from .env file.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME:    str = "SevaSetu"
    APP_VERSION: str = "3.0.0"
    DEBUG:       bool = True

    DATABASE_URL: str = "sqlite:///./sevasetu.db"

    SECRET_KEY:                  str = "changeme-super-secret-key-32chars!"
    ALGORITHM:                   str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    KNOWLEDGE_BASE_PATH: str = "./data/schemes_cleaned.json"
    FAISS_INDEX_PATH:    str = "./data/faiss.index"

    # ── LLM Provider ──────────────────────────────────────────────────────────
    # "groq"     → cloud Groq API (default)
    # "together" → Together AI hosted fine-tuned model (Option B)
    # "ollama"   → local fine-tuned model via Ollama (Options C/D)
    LLM_PROVIDER: str = "groq"

    # Groq settings
    GROQ_API_KEY:    str = ""
    LLM_MODEL:       str = "llama-3.3-70b-versatile"
    LLM_MODEL_FAST:  str = "llama-3.1-8b-instant"
    LLM_MAX_TOKENS:  int = 700
    LLM_TEMPERATURE: float = 0.4

    # Together AI settings (used after Option B fine-tuning)
    TOGETHER_API_KEY: str = ""
    TOGETHER_MODEL:   str = ""   # Set to your fine-tuned model ID after training

    # Ollama settings (used after Options C/D fine-tuning)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL:    str = "sevasetu"

    # HuggingFace (for dataset upload in Option C)
    HF_TOKEN:    str = ""
    HF_USERNAME: str = ""

    AUDIO_OUTPUT_DIR: str = "./static/audio"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
