"""DTOs for resume draft flow."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResumeDraftProgressDTO:
    """DTO representing current draft progress."""

    draft_id: str
    conversation_id: str
    current_step: str
    status: str
    missing_fields: tuple[str, ...]
    collected: dict[str, Any] = field(default_factory=dict)
    next_question: str | None = None
    ready_to_finalize: bool = False
    loaded_resume_title: str | None = None

