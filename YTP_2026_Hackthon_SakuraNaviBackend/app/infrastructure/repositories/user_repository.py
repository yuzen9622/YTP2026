"""SQLAlchemy implementation of UserRepository."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user.entity import User
from app.domains.user.value_objects import (
    Account,
    Email,
    HashedPassword,
    Phone,
    UserId,
    UserName,
)
from app.infrastructure.auth.phone_encryption_service import phone_encryption_service
from app.infrastructure.db.models.user import UserModel


class UserRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: UserId) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == id.value)
        )
        row = result.scalar_one_or_none()
        return self._reconstruct(row) if row else None

    async def find_by_account(self, account: Account) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.account == account.value)
        )
        row = result.scalar_one_or_none()
        return self._reconstruct(row) if row else None

    async def find_by_email(self, email: Email) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email.value)
        )
        row = result.scalar_one_or_none()
        return self._reconstruct(row) if row else None

    async def save(self, user: User) -> None:
        """Persist a user (insert or update) via session.merge().

        merge() consults the session identity map first (no extra SELECT when
        the object was already loaded in this unit-of-work) and falls back to
        a single SELECT+INSERT/UPDATE otherwise.
        """
        phone_plain = user.phone().value if user.phone() else None
        phone_encrypted = phone_encryption_service.encrypt(phone_plain) if phone_plain else None
        phone_hmac = phone_encryption_service.compute_hmac(phone_plain) if phone_plain else None

        row = UserModel(
            id=user.id().value,
            name=user.name().value,
            account=user.account().value,
            hashed_password=user.hashed_password().value,
            email=user.email().value if user.email() else None,
            phone=phone_encrypted,
            phone_hmac=phone_hmac,
            bio=user.bio().value,
            birth_date=user.birth_date().value if user.birth_date() else None,
            career=user.career().value.value if user.career() else None,
            tags=list(user.tags().value) if user.tags().value else None,
            avatar_url=user.avatar_url().value if user.avatar_url() else None,
            language_skills=[
                {"language": s.language, "proficiency": s.proficiency.value}
                for s in user.language_skills().value
            ] if user.language_skills().value else None,
            registered_address=user.registered_address(),
            residential_address=user.residential_address(),
            is_residential_same_as_registered=user.is_residential_same_as_registered(),
            is_active=user.is_active(),
            gender=user.gender().value.value if user.gender() else None,
            role=user.role().value.value if hasattr(user.role(), "value") else str(user.role()),
            deleted_at=user.deleted_at(),
            created_at=user.created_at(),
            updated_at=user.updated_at(),
        )
        await self._session.merge(row)

    async def exists_by_account(self, account: Account) -> bool:
        result = await self._session.execute(
            select(UserModel.id).where(UserModel.account == account.value)
        )
        return result.scalar_one_or_none() is not None

    async def exists_by_email(self, email: Email) -> bool:
        result = await self._session.execute(
            select(UserModel.id).where(UserModel.email == email.value)
        )
        return result.scalar_one_or_none() is not None

    async def exists_by_phone(self, phone: Phone) -> bool:
        phone_hmac = phone_encryption_service.compute_hmac(phone.value)
        result = await self._session.execute(
            select(UserModel.id).where(UserModel.phone_hmac == phone_hmac)
        )
        return result.scalar_one_or_none() is not None

    async def find_taken_fields(
        self,
        account: Account,
        email: Optional[Email] = None,
        phone: Optional[Phone] = None,
    ) -> frozenset[str]:
        """Check account/email/phone uniqueness in a single query."""
        email_val = email.value if email else None
        phone_hmac = phone_encryption_service.compute_hmac(phone.value) if phone else None

        conditions = [UserModel.account == account.value]
        if email_val:
            conditions.append(UserModel.email == email_val)
        if phone_hmac:
            conditions.append(UserModel.phone_hmac == phone_hmac)

        result = await self._session.execute(
            select(UserModel.account, UserModel.email, UserModel.phone_hmac)
            .where(or_(*conditions))
        )
        rows = result.all()

        taken: set[str] = set()
        for row in rows:
            if row.account == account.value:
                taken.add("account")
            if email_val and row.email == email_val:
                taken.add("email")
            if phone_hmac and row.phone_hmac == phone_hmac:
                taken.add("phone")
        return frozenset(taken)

    @staticmethod
    def _reconstruct(row: UserModel) -> User:
        phone_plain: Optional[str] = None
        if row.phone:
            phone_plain = phone_encryption_service.decrypt(row.phone)

        return User._restore(
            id=UserId(row.id),
            name=UserName(row.name),
            account=Account(row.account),
            hashed_password=HashedPassword(row.hashed_password),
            email=Email(row.email) if row.email else None,
            phone=Phone(phone_plain) if phone_plain else None,
            bio=row.bio,
            created_at=row.created_at,
            updated_at=row.updated_at,
            is_active=row.is_active,
            deleted_at=row.deleted_at,
            birth_date=row.birth_date,
            career=row.career,
            tags=list(row.tags) if row.tags else None,
            avatar_url=row.avatar_url,
            language_skills=[
                (s["language"], s["proficiency"])
                for s in row.language_skills
            ] if row.language_skills else None,
            registered_address=row.registered_address,
            residential_address=row.residential_address,
            is_residential_same_as_registered=row.is_residential_same_as_registered,
            gender=row.gender,
            role=row.role,
        )

    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        """List users with pagination and optional filters."""
        base_query = select(UserModel)
        count_query = select(func.count(UserModel.id))

        conditions = []
        if search:
            pattern = f"%{search}%"
            conditions.append(
                or_(
                    UserModel.name.ilike(pattern),
                    UserModel.account.ilike(pattern),
                    UserModel.email.ilike(pattern),
                )
            )
        if is_active is not None:
            conditions.append(UserModel.is_active == is_active)

        if conditions:
            base_query = base_query.where(*conditions)
            count_query = count_query.where(*conditions)

        base_query = base_query.order_by(UserModel.created_at.desc()).limit(limit).offset(offset)

        rows_result = await self._session.execute(base_query)
        rows = rows_result.scalars().all()

        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        return [self._reconstruct(row) for row in rows], int(total)
