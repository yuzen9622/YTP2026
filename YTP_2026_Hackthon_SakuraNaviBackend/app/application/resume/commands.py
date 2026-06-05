"""Command objects for resume write operations."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class CreateResumeCommand:
    """Command for creating a new resume."""
    user_id: str
    title: str
    summary: Optional[str] = None
    skills: tuple = field(default_factory=tuple)
    work_experiences: tuple = field(default_factory=tuple)
    external_links: tuple = field(default_factory=tuple)
    expected_salary: Optional[dict] = None
    work_time_range: Optional[dict] = None


@dataclass(frozen=True)
class UpdateResumeCommand:
    """Command for partially updating a resume.

    Only fields listed in ``provided_fields`` will be applied.
    """
    user_id: str
    resume_id: str
    provided_fields: frozenset
    title: Optional[str] = None
    summary: Optional[str] = None
    skills: tuple = field(default_factory=tuple)
    work_experiences: tuple = field(default_factory=tuple)
    external_links: tuple = field(default_factory=tuple)
    expected_salary: Optional[dict] = None
    work_time_range: Optional[dict] = None


@dataclass(frozen=True)
class SetPrimaryResumeCommand:
    """Command for setting a resume as the primary one."""
    user_id: str
    resume_id: str
