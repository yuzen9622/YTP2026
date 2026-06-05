"""Repository interface for admin aggregate persistence."""
from typing import Optional, Protocol

from app.domains.admin.entity import Admin
from app.domains.admin.value_objects import AdminId


class AdminRepository(Protocol):
    async def find_by_id(self, id: AdminId) -> Optional[Admin]: ...

    async def find_by_account(self, account: str) -> Optional[Admin]: ...

    async def save(self, admin: Admin) -> None: ...

    async def delete(self, admin_id: AdminId) -> None: ...

    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        is_active: bool = True,
    ) -> tuple[list[Admin], int]: ...

    async def exists_by_account(self, account: str) -> bool: ...