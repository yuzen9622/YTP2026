"""Command objects for resume draft use cases."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StartResumeDraftCommand:
    """Start or load an active draft."""

    user_id: str
    conversation_id: str


@dataclass(frozen=True)
class UpdateResumeDraftCommand:
    """Patch one or more fields in an active draft."""

    user_id: str
    conversation_id: str
    patch: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FinalizeResumeDraftCommand:
    """Finalize an active draft into a real resume."""

    user_id: str
    conversation_id: str


@dataclass(frozen=True)
class LoadResumeForEditCommand:
    """Load an existing resume into the draft session for editing."""

    user_id: str
    conversation_id: str
    resume_id: str
