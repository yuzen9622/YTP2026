"""SQLAlchemy implementation of AdminRepository."""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.entity import Admin
from app.domains.admin.value_objects import AdminId
from app.infrastructure.db.models.admin import AdminModel


class AdminRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: AdminId) -> Optional[Admin]:
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.id == id.value)
        )
        row = result.scalar_one_or_none()
        return self._reconstruct(row) if row else None

    async def find_by_account(self, account: str) -> Optional[Admin]:
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.account == account)
        )
        row = result.scalar_one_or_none()
        return self._reconstruct(row) if row else None

    async def save(self, admin: Admin) -> None:
        row = AdminModel(
            id=admin.id().value,
            account=admin.account(),
            hashed_password=admin.hashed_password(),
            role=admin.role().value.value if hasattr(admin.role().value, "value") else admin.role().value,
            is_active=admin.is_active(),
            created_at=admin.created_at(),
            updated_at=admin.updated_at(),
        )
        await self._session.merge(row)

    async def delete(self, admin_id: AdminId) -> None:
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.id == admin_id.value).limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            await self._session.delete(row)

    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        is_active: bool = True,
    ) -> tuple[list[Admin], int]:
        base_query = select(AdminModel).where(AdminModel.is_active == is_active)
        count_query = select(func.count(AdminModel.id)).where(AdminModel.is_active == is_active)

        base_query = base_query.order_by(AdminModel.created_at.desc()).limit(limit).offset(offset)

        rows_result = await self._session.execute(base_query)
        rows = rows_result.scalars().all()

        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        return [self._reconstruct(row) for row in rows], int(total)

    async def exists_by_account(self, account: str) -> bool:
        result = await self._session.execute(
            select(AdminModel.id).where(AdminModel.account == account)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _reconstruct(row: AdminModel) -> Admin:
        return Admin._restore(
            id=AdminId(row.id),
            account=row.account,
            hashed_password=row.hashed_password,
            role=row.role,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )