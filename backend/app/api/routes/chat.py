"""
api/routes/chat.py – Conversation and message endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.orm import Conversation, Message, User
from app.services import rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class MessageRequest(BaseModel):
    message: str
    language: str = "hindi"
    mode: str = "beginner"
    conversation_id: Optional[int] = None
    voice_output: bool = False


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    language: str
    audio_url: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: str
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_dt(dt) -> str:
    return dt.isoformat() if dt else ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/message")
def send_message(
    req: MessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get or create conversation
    if req.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == req.conversation_id,
            Conversation.user_id == current_user.id,
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = Conversation(
            user_id=current_user.id,
            title=req.message[:60] + ("…" if len(req.message) > 60 else ""),
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.message,
        language=req.language,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # RAG pipeline
    reply_text, snippets, detected_lang = rag_service.process_chat(
        message=req.message,
        language=req.language,
        mode=req.mode,
    )

    # Optional TTS
    audio_url = None
    if req.voice_output:
        try:
            from app.services.voice_service import text_to_speech
            from app.core.config import settings
            audio_url = text_to_speech(reply_text, detected_lang, settings.AUDIO_OUTPUT_DIR)
        except Exception as e:
            print(f"TTS error: {e}")

    # Save assistant message
    bot_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=reply_text,
        language=detected_lang,
        audio_url=audio_url,
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    return {
        "message_id": bot_msg.id,
        "reply": reply_text,
        "language": detected_lang,
        "conversation_id": conv.id,
        "retrieved_schemes": snippets,
        "audio_url": audio_url,
    }


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [
        {"id": c.id, "title": c.title, "created_at": _fmt_dt(c.created_at)}
        for c in convs
    ]


@router.get("/conversations/{conv_id}")
def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": _fmt_dt(conv.created_at),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "language": m.language,
                "audio_url": m.audio_url,
                "created_at": _fmt_dt(m.created_at),
            }
            for m in conv.messages
        ],
    }


@router.delete("/conversations/{conv_id}", status_code=204)
def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
