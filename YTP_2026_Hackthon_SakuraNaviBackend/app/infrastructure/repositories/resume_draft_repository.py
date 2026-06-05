"""SQLAlchemy implementation of ResumeDraftRepository."""
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.resume_draft.entity import ResumeDraft
from app.domains.resume_draft.value_objects import ResumeDraftId
from app.infrastructure.db.models.resume_draft import ResumeDraftModel


class ResumeDraftRepositoryImpl:
    """Persist and retrieve resume draft aggregates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_active_by_user_and_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> ResumeDraft | None:
        result = await self._session.execute(
            select(ResumeDraftModel).where(
                ResumeDraftModel.user_id == uuid.UUID(user_id),
                ResumeDraftModel.conversation_id == uuid.UUID(conversation_id),
                ResumeDraftModel.status == "active",
            )
        )
        row = result.scalar_one_or_none()
        return self._reconstruct(row) if row else None

    async def save(self, draft: ResumeDraft) -> None:
        row = ResumeDraftModel(
            id=draft.id().value,
            user_id=uuid.UUID(draft.user_id()),
            conversation_id=uuid.UUID(draft.conversation_id()),
            payload_json=draft.payload_json(),
            current_step=draft.current_step().value,
            status=draft.status().value,
            created_at=draft.created_at(),
            updated_at=draft.updated_at(),
        )
        await self._session.merge(row)

    async def delete(self, draft_id: ResumeDraftId) -> None:
        await self._session.execute(
            delete(ResumeDraftModel).where(ResumeDraftModel.id == draft_id.value)
        )

    @staticmethod
    def _reconstruct(row: ResumeDraftModel) -> ResumeDraft:
        return ResumeDraft._restore(
            id=ResumeDraftId(row.id),
            user_id=str(row.user_id),
            conversation_id=str(row.conversation_id),
            payload_json=row.payload_json or {},
            current_step=row.current_step,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
