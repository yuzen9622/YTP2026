"""Value objects for ResumeDraft domain."""
import enum
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeDraftId:
    """Resume draft entity unique identifier."""
    value: uuid.UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise ValueError(f"Invalid ResumeDraftId: {self.value}")


class ResumeDraftStep(str, enum.Enum):
    """Guided draft steps."""
    TITLE = "title"
    SUMMARY = "summary"
    SKILLS = "skills"
    WORK_EXPERIENCES = "work_experiences"
    READY_TO_FINALIZE = "ready_to_finalize"


class ResumeDraftStatus(str, enum.Enum):
    """Draft lifecycle status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
