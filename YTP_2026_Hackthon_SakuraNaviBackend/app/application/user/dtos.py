"""Data Transfer Objects for user-related data."""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class UserProfileDTO:
    """DTO containing user profile data for API responses."""
    id: str
    name: str
    account: str
    email: Optional[str]
    phone: Optional[str]
    bio: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    birth_date: Optional[date] = None
    career: Optional[str] = None
    tags: tuple = field(default_factory=tuple)
    avatar_url: Optional[str] = None
    language_skills: tuple = field(default_factory=tuple)
    registered_address: Optional[str] = None
    residential_address: Optional[str] = None
    is_residential_same_as_registered: bool = False
    gender: Optional[str] = None
    role: str = "user"


@dataclass(frozen=True)
class TokenPairDTO:
    """DTO containing authentication token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class PaginatedUsersDTO:
    """Paginated list of users for admin API."""
    items: list[UserProfileDTO]
    total: int
    limit: int
    offset: int
