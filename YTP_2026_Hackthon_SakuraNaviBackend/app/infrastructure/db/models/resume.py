"""SQLAlchemy ORM model for the resumes table."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastructure.db.base import Base


class ResumeModel(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # [{"name": "...", "level": "..."}]
    work_experiences: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    external_links: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # [{"label": "...", "url": "..."}]
    expected_salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_salary_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    work_time_range: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"start_time": "09:00", "end_time": "18:00", "work_time_type": "full_time"}
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
