"""Data Transfer Objects for admin operations."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AdminDTO:
    """DTO for admin data."""
    id: str
    account: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AdminListDTO:
    """Paginated admin list."""
    items: list[AdminDTO]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class AdminAuthDTO:
    """DTO for admin authentication result."""
    id: str
    account: str
    role: str
    access_token: str