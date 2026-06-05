"""ResumeRepository protocol — interface for resume persistence."""
from typing import Protocol

from app.domains.resume.entity import Resume
from app.domains.resume.value_objects import ResumeId


class ResumeRepository(Protocol):
    """Protocol defining the contract for resume persistence operations."""

    async def find_by_id(self, id: ResumeId) -> Resume | None:
        """Find a resume by its ID."""
        ...

    async def find_by_user_id(self, user_id: str) -> list[Resume]:
        """Find all resumes belonging to a user, ordered by is_primary desc, created_at desc."""
        ...

    async def save(self, resume: Resume) -> None:
        """Insert or update a resume."""
        ...

    async def delete(self, id: ResumeId, user_id: str) -> None:
        """Delete a resume by ID (only if it belongs to the given user)."""
        ...

    async def set_primary(self, id: ResumeId, user_id: str) -> None:
        """Set a resume as primary (unsets all other primaries for the user)."""
        ...

    async def find_primary_by_user_id(self, user_id: str) -> Resume | None:
        """Find the primary resume for a user."""
        ...
