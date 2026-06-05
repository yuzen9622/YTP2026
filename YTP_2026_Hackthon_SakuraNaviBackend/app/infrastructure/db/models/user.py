"""SQLAlchemy ORM model for the users table."""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastructure.db.base import Base

_DEFAULT_BIO = "這位使用者尚未填寫個人簡介。"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # Fernet-encrypted E.164
    phone_hmac: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)  # HMAC-SHA256 for lookups
    bio: Mapped[str] = mapped_column(Text, nullable=False, default=_DEFAULT_BIO)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    career: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String(50)), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    language_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # [{"language": "en", "proficiency": "advanced"}, ...]
    registered_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    residential_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_residential_same_as_registered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
