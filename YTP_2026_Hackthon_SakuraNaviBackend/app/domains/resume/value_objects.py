"""Value objects for the Resume domain."""
import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TypeAlias


@dataclass(frozen=True)
class ResumeId:
    """Resume entity unique identifier."""
    value: uuid.UUID

    def __post_init__(self):
        if not isinstance(self.value, uuid.UUID):
            raise ValueError(f"Invalid ResumeId: {self.value}")


@dataclass(frozen=True)
class ResumeTitle:
    """Resume title value object."""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("Resume title cannot be empty")
        if len(self.value) > 100:
            raise ValueError("Resume title cannot exceed 100 characters")


@dataclass(frozen=True)
class ResumeSummary:
    """Resume summary/簡述 value object."""
    value: str

    def __post_init__(self):
        if len(self.value) > 2000:
            raise ValueError("Resume summary cannot exceed 2000 characters")


@dataclass(frozen=True)
class ResumeSkill:
    """A single skill item on a resume."""
    name: str
    level: str  # e.g., "beginner", "intermediate", "advanced", "expert"

    def __post_init__(self):
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Skill name cannot be empty")
        if len(self.name) > 50:
            raise ValueError("Skill name cannot exceed 50 characters")


@dataclass(frozen=True)
class ResumeSkills:
    """Resume skills value object (immutable tuple)."""
    value: tuple[ResumeSkill, ...]

    def __post_init__(self):
        if len(self.value) > 50:
            raise ValueError("Resume skills cannot exceed 50 items")


class WorkTimeType(str, enum.Enum):
    """工作時間類型"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


@dataclass(frozen=True)
class WorkTimeRange:
    """工作時間段 value object."""
    start_time: str  # e.g., "09:00"
    end_time: str    # e.g., "18:00"
    work_time_type: WorkTimeType

    def __post_init__(self):
        if not isinstance(self.work_time_type, WorkTimeType):
            raise ValueError(f"Invalid work time type: {self.work_time_type}")


@dataclass(frozen=True)
class WorkExperience:
    """工作經驗 value object."""
    company: str
    position: str
    description: str
    start_date: str  # YYYY-MM format
    end_date: str    # YYYY-MM format or "present"
    is_current: bool = False

    def __post_init__(self):
        if not self.company or len(self.company.strip()) == 0:
            raise ValueError("Company name cannot be empty")
        if len(self.company) > 100:
            raise ValueError("Company name cannot exceed 100 characters")


@dataclass(frozen=True)
class ExternalLink:
    """外部連結 value object."""
    label: str  # e.g., "GitHub", "LinkedIn"
    url: str

    def __post_init__(self):
        if not self.label or len(self.label.strip()) == 0:
            raise ValueError("Link label cannot be empty")
        if len(self.label) > 50:
            raise ValueError("Link label cannot exceed 50 characters")
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("External link URL must start with http:// or https://")
        if len(self.url) > 512:
            raise ValueError("External link URL cannot exceed 512 characters")


@dataclass(frozen=True)
class ExpectedSalary:
    """期望薪資 value object."""
    min: int
    max: int
    currency: str  # e.g., "TWD", "USD", "JPY"

    def __post_init__(self):
        if not isinstance(self.min, int) or self.min < 0:
            raise ValueError("Minimum salary cannot be negative")
        if not isinstance(self.max, int) or self.max < 0:
            raise ValueError("Maximum salary cannot be negative")
        if self.min > self.max:
            raise ValueError("Minimum salary cannot be greater than maximum salary")
        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")


@dataclass(frozen=True)
class ResumeTimestamp:
    """Timestamp value object (used for both created_at and updated_at)."""
    value: datetime

    def __post_init__(self):
        if not isinstance(self.value, datetime):
            raise ValueError("Timestamp must be a datetime")
        if self.value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")


ResumeCreatedAt: TypeAlias = ResumeTimestamp
ResumeUpdatedAt: TypeAlias = ResumeTimestamp
