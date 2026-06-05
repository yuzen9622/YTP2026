"""Repository interface for user aggregate persistence."""
from typing import Optional, Protocol

from app.domains.user.entity import User
from app.domains.user.value_objects import Account, Email, Phone, UserId


class UserRepository(Protocol):
    async def find_by_id(self, id: UserId) -> Optional[User]: ...
    async def find_by_account(self, account: Account) -> Optional[User]: ...
    async def find_by_email(self, email: Email) -> Optional[User]: ...
    async def save(self, user: User) -> None: ...
    async def exists_by_account(self, account: Account) -> bool: ...
    async def exists_by_email(self, email: Email) -> bool: ...
    async def exists_by_phone(self, phone: Phone) -> bool: ...
    async def find_taken_fields(
        self,
        account: Account,
        email: Optional[Email] = None,
        phone: Optional[Phone] = None,
    ) -> frozenset[str]:
        """Return the set of field names ('account'/'email'/'phone') already in use.

        Consolidates up to three uniqueness checks into one query.
        """
        ...

    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        """List users with pagination and optional filters. Returns (users, total_count)."""
        ...
