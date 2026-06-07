"""
main.py  –  FastAPI application factory.

Startup sequence:
  1. Create DB tables
  2. Seed schemes from JSON dataset
  3. Build / load FAISS index
  4. Mount static files
  5. Register API routers
"""
import os
import json
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.session import engine, SessionLocal
from app.models.orm import Base, Scheme
from app.services import rag_service, telegram_service
from app.api.routes import auth, chat, schemes, voice, admin


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run initialization tasks before the server starts serving requests."""
    setup_logging(debug=settings.DEBUG)
    print("🚀 SevaSetu starting up…")

    # 1. Create all DB tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready")

    # 2. Seed schemes from JSON dataset
    _seed_schemes()
    print("✅ Scheme knowledge base seeded")

    # 3. Build / load FAISS index
    rag_service.initialize_rag(
        knowledge_base_path=settings.KNOWLEDGE_BASE_PATH,
        index_path=settings.FAISS_INDEX_PATH,
    )

    # 4. Ensure audio output directory exists
    Path(settings.AUDIO_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    # Also ensure static root exists for StaticFiles mount
    Path("static").mkdir(exist_ok=True)

    # 5. Start Telegram long polling (only if a bot token is configured)
    telegram_service.start_polling()

    yield   # ← server is running

    print("🛑 SevaSetu shutting down…")
    await telegram_service.stop_polling()


def _seed_schemes():
    """Insert schemes from the JSON dataset if the table is empty."""
    kb_path = settings.KNOWLEDGE_BASE_PATH
    if not Path(kb_path).exists():
        print(f"⚠️  Dataset not found at {kb_path}. Skipping seed.")
        return

    db = SessionLocal()
    try:
        if db.query(Scheme).count() > 0:
            return   # already seeded

        with open(kb_path, encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            scheme = Scheme(
                external_id=item["id"],
                name=item["scheme"],
                english_desc=item.get("english"),
                hindi_desc=item.get("hindi"),
                bhojpuri_desc=item.get("bhojpuri"),
                benefits=json.dumps(item.get("benefits"), ensure_ascii=False) if isinstance(item.get("benefits"), dict) else item.get("benefits"),
                eligibility=json.dumps(item.get("eligibility"), ensure_ascii=False) if isinstance(item.get("eligibility"), dict) else item.get("eligibility"),
                age_limit=item.get("age_limit"),
                contribution_type=item.get("contribution_type"),
                pension_range=item.get("pension_range"),
            )
            db.add(scheme)
        db.commit()
        print(f"  Seeded {len(data)} schemes into the database.")
    finally:
        db.close()


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Multilingual AI Chatbot for Indian Government Services",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure static root exists before StaticFiles is mounted
    static_root = Path("static")
    static_root.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_root), html=False), name="static")

    # API routers
    prefix = "/api/v1"
    app.include_router(auth.router,    prefix=prefix)
    app.include_router(chat.router,    prefix=prefix)
    app.include_router(schemes.router, prefix=prefix)
    app.include_router(voice.router,   prefix=prefix)
    app.include_router(admin.router,   prefix=prefix)
    # Telegram integration runs via long polling (see lifespan / telegram_service),
    # so no webhook router is registered.

    @app.get("/health")
    def health():
        return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
