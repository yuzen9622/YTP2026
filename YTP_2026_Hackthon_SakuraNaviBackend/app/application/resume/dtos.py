"""Data Transfer Objects for resume-related data."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ResumeDTO:
    """DTO containing resume data for API responses."""
    id: str
    user_id: str
    title: str
    summary: Optional[str]
    skills: tuple
    work_experiences: tuple
    external_links: tuple
    expected_salary: Optional[dict]
    work_time_range: Optional[dict]
    is_primary: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ResumeWithUserDTO:
    """DTO containing resume data plus associated user identity fields."""
    id: str
    user_id: str
    user_name: str
    user_email: Optional[str]
    user_phone: Optional[str]
    title: str
    summary: Optional[str]
    skills: tuple
    work_experiences: tuple
    external_links: tuple
    expected_salary: Optional[dict]
    work_time_range: Optional[dict]
    is_primary: bool
    created_at: datetime
    updated_at: datetime
