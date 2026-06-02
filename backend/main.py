"""
main.py – SevaSetu FastAPI application entry point (v2)
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.session import engine
from app.models.orm import Base
from app.services import rag_service
from app.api.routes import auth, chat, schemes, voice, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    # Create DB tables
    Base.metadata.create_all(bind=engine)

    # Create static audio dir
    os.makedirs(settings.AUDIO_OUTPUT_DIR, exist_ok=True)

    # Initialize RAG (loads cleaned JSON dataset)
    rag_service.initialize_rag(
        knowledge_base_path=settings.KNOWLEDGE_BASE_PATH,
        index_path=settings.FAISS_INDEX_PATH,
    )

    yield
    # ── Shutdown (nothing needed) ─────────────────────────────────────────────


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multilingual AI chatbot for Bihar government welfare schemes",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (TTS audio) ──────────────────────────────────────────────────
os.makedirs("./static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="./static"), name="static")

# ── Routes ────────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(auth.router,    prefix=PREFIX)
app.include_router(chat.router,    prefix=PREFIX)
app.include_router(schemes.router, prefix=PREFIX)
app.include_router(voice.router,   prefix=PREFIX)
app.include_router(admin.router,   prefix=PREFIX)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
