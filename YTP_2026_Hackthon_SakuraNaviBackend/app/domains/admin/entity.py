"""Admin aggregate root — standalone admin credentials, no user link."""
from dataclasses import dataclass
from datetime import datetime

from app.domains.admin.value_objects import AdminId, AdminRole


@dataclass
class Admin:
    """Admin aggregate root.

    Standalone admin identity — has account + hashed_password only.
    No link to users table.
    """
    _id: AdminId
    _account: str
    _hashed_password: str
    _role: AdminRole
    _is_active: bool
    _created_at: datetime
    _updated_at: datetime

    def id(self) -> AdminId:
        return self._id

    def account(self) -> str:
        return self._account

    def hashed_password(self) -> str:
        return self._hashed_password

    def role(self) -> AdminRole:
        return self._role

    def is_active(self) -> bool:
        return self._is_active

    def created_at(self) -> datetime:
        return self._created_at

    def updated_at(self) -> datetime:
        return self._updated_at

    def update_role(self, new_role: AdminRole, now: datetime) -> None:
        self._role = new_role
        self._updated_at = now

    def deactivate(self, now: datetime) -> None:
        self._is_active = False
        self._updated_at = now

    def activate(self, now: datetime) -> None:
        self._is_active = True
        self._updated_at = now

    def change_password(self, hashed_password: str, now: datetime) -> None:
        self._hashed_password = hashed_password
        self._updated_at = now

    # --- Persistence reconstruction ---

    @classmethod
    def _restore(
        cls,
        *,
        id: AdminId,
        account: str,
        hashed_password: str,
        role: str,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Admin":
        obj: "Admin" = cls.__new__(cls)
        obj._id = id
        obj._account = account
        obj._hashed_password = hashed_password
        try:
            obj._role = AdminRole(role)
        except ValueError:
            raise ValueError(f"Invalid admin role: '{role}'. Must be one of: {[r.value for r in AdminRole]}")
        obj._is_active = is_active
        obj._created_at = created_at
        obj._updated_at = updated_at
        return obj