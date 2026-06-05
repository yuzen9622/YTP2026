"""ResumeDraftRepository protocol."""
from typing import Protocol

from app.domains.resume_draft.entity import ResumeDraft
from app.domains.resume_draft.value_objects import ResumeDraftId


class ResumeDraftRepository(Protocol):
    """Persistence contract for resume drafts."""

    async def find_active_by_user_and_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> ResumeDraft | None:
        """Find the active draft for the user within one conversation."""
        ...

    async def save(self, draft: ResumeDraft) -> None:
        """Insert or update a draft."""
        ...

    async def delete(self, draft_id: ResumeDraftId) -> None:
        """Hard-delete a draft."""
        ...
