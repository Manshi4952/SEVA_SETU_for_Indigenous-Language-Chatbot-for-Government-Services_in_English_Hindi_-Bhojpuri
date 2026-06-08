"""
api/routes/admin.py – Admin-only endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db
from app.models.orm import Conversation, Message, Scheme, User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return {
        "users": db.query(User).count(),
        "conversations": db.query(Conversation).count(),
        "messages": db.query(Message).count(),
        "schemes": db.query(Scheme).count(),
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    users = db.query(User).all()
    return [
        {"id": u.id, "full_name": u.full_name, "email": u.email,
         "role": u.role, "preferred_lang": u.preferred_lang,
         "created_at": u.created_at.isoformat() if u.created_at else ""}
        for u in users
    ]
