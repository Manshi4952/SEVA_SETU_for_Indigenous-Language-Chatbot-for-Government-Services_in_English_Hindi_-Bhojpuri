"""
models/orm.py – SQLAlchemy ORM models.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    full_name      = Column(String(120), nullable=False)
    email          = Column(String(255), unique=True, index=True, nullable=False)
    phone          = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    preferred_lang = Column(String(20), default="hindi")
    role           = Column(String(20), default="user")   # user | admin
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime(timezone=True), default=_now)

    conversations  = relationship("Conversation", back_populates="user", cascade="all, delete")


class Conversation(Base):
    __tablename__ = "conversations"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String(255), default="New Conversation")
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    user     = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete",
                            order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id              = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role            = Column(String(20), nullable=False)   # user | assistant
    content         = Column(Text, nullable=False)
    language        = Column(String(20), default="hindi")
    audio_url       = Column(String(500), nullable=True)
    created_at      = Column(DateTime(timezone=True), default=_now)

    conversation = relationship("Conversation", back_populates="messages")


class Scheme(Base):
    __tablename__ = "schemes"

    id                = Column(Integer, primary_key=True, index=True)
    external_id       = Column(String(50), unique=True, index=True)
    name              = Column(String(255), nullable=False)
    english_desc      = Column(Text, nullable=True)
    hindi_desc        = Column(Text, nullable=True)
    bhojpuri_desc     = Column(Text, nullable=True)
    benefits          = Column(Text, nullable=True)   # stored as JSON string
    eligibility       = Column(Text, nullable=True)
    age_limit         = Column(String(100), nullable=True)
    contribution_type = Column(String(100), nullable=True)
    pension_range     = Column(String(100), nullable=True)
    created_at        = Column(DateTime(timezone=True), default=_now)
