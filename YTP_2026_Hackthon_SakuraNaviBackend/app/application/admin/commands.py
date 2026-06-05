"""Command objects for admin operations."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RegisterAdminCommand:
    """Command to register a new standalone admin account."""
    account: str
    password: str
    role: str  # superadmin / customer_service / security_reviewer / content_manager


@dataclass(frozen=True)
class AuthenticateAdminCommand:
    """Command to authenticate an admin with account + password."""
    account: str
    password: str


@dataclass(frozen=True)
class UpdateAdminCommand:
    """Command to update an admin's role, active status, or password."""
    admin_id: str
    role: Optional[str] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = None


@dataclass(frozen=True)
class RemoveAdminCommand:
    """Command to remove an admin by admin_id."""
    admin_id: str