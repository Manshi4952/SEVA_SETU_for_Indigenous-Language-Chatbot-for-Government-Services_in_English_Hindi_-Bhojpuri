"""
core/logging_config.py – Central logging setup.

Provides a dedicated "sevasetu.ai" logger for everything related to AI:
retrieval decisions, LLM requests/responses, latency, token usage and errors.
Logs go to both the console and a rotating file at `logs/ai.log`.

Call `setup_logging()` once at startup, then `get_ai_logger()` anywhere.
"""
from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

AI_LOGGER_NAME = "sevasetu.ai"
_LOG_DIR = Path("logs")
_LOG_FILE = _LOG_DIR / "ai.log"

_configured = False


def setup_logging(debug: bool = False) -> None:
    """Configure the AI logger with console + rotating file handlers."""
    global _configured
    if _configured:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if debug else logging.INFO
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(AI_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False  # don't double-log via the root logger

    # Avoid duplicate handlers on reload.
    if not logger.handlers:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        console.setLevel(level)
        logger.addHandler(console)

        file_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        file_handler.setLevel(logging.DEBUG)  # keep full detail on disk
        logger.addHandler(file_handler)

    _configured = True
    logger.info("AI logging initialized (level=%s, file=%s)",
                logging.getLevelName(level), _LOG_FILE)


def get_ai_logger() -> logging.Logger:
    """Return the shared AI logger (configures lazily if needed)."""
    if not _configured:
        setup_logging()
    return logging.getLogger(AI_LOGGER_NAME)
