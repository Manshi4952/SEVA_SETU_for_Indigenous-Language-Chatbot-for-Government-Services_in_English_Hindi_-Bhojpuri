"""
api/routes/schemes.py – Scheme listing and search endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.orm import Scheme

router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.get("/")
def list_schemes(
    language: str = Query("hindi"),
    q: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Scheme)
    if q:
        q_lower = f"%{q.lower()}%"
        query = query.filter(Scheme.name.ilike(q_lower))
    schemes = query.offset(skip).limit(limit).all()

    desc_field = {
        "hindi": "hindi_desc",
        "bhojpuri": "bhojpuri_desc",
        "english": "english_desc",
    }.get(language, "hindi_desc")

    return [
        {
            "id": s.external_id or str(s.id),
            "name": s.name,
            "description": getattr(s, desc_field) or s.english_desc or "",
            "age_limit": s.age_limit,
            "pension_range": s.pension_range,
        }
        for s in schemes
    ]


@router.get("/{scheme_id}")
def get_scheme(scheme_id: str, db: Session = Depends(get_db)):
    scheme = db.query(Scheme).filter(Scheme.external_id == scheme_id).first()
    if not scheme:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Scheme not found")
    return {
        "id": scheme.external_id,
        "name": scheme.name,
        "english": scheme.english_desc,
        "hindi": scheme.hindi_desc,
        "bhojpuri": scheme.bhojpuri_desc,
        "benefits": scheme.benefits,
        "eligibility": scheme.eligibility,
        "age_limit": scheme.age_limit,
        "pension_range": scheme.pension_range,
    }
