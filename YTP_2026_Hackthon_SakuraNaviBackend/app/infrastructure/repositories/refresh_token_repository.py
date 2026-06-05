"""SQLAlchemy implementation of RefreshTokenRepository."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.refresh_token import RefreshTokenModel


class RefreshTokenRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, jti: str, user_id: str, expires_at: datetime, family_id: str) -> None:
        row = RefreshTokenModel(
            id=uuid.uuid4(),
            jti=jti,
            user_id=uuid.UUID(user_id),
            family_id=uuid.UUID(family_id),
            is_revoked=False,
            expires_at=expires_at,
        )
        self._session.add(row)

    async def exists_and_valid(self, jti: str) -> bool:
        result = await self._session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.jti == jti,
                RefreshTokenModel.is_revoked.is_(False),
                RefreshTokenModel.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none() is not None

    async def revoke(self, jti: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.jti == jti)
            .values(is_revoked=True)
        )

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == uuid.UUID(user_id))
            .values(is_revoked=True)
        )

    async def find_family_id_by_jti(self, jti: str) -> Optional[str]:
        result = await self._session.execute(
            select(RefreshTokenModel.family_id).where(RefreshTokenModel.jti == jti)
        )
        row = result.scalar_one_or_none()
        return str(row) if row else None

    async def revoke_family(self, family_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.family_id == uuid.UUID(family_id))
            .values(is_revoked=True)
        )
