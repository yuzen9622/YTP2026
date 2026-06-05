"""Command objects for write operations."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class ListAllUsersQuery:
    """Query for listing all users with pagination and filters."""
    limit: int = 20
    offset: int = 0
    search: Optional[str] = None
    is_active: Optional[bool] = None


@dataclass(frozen=True)
class RegisterUserCommand:
    """Command for registering a new user."""
    name: str
    account: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    career: Optional[str] = None
    tags: tuple = field(default_factory=tuple)
    gender: Optional[str] = None


@dataclass(frozen=True)
class LoginCommand:
    """Command for user login."""
    account: str
    password: str


@dataclass(frozen=True)
class RefreshTokenCommand:
    """Command for refreshing an access token."""
    refresh_token: str


@dataclass(frozen=True)
class UpdateProfileCommand:
    """Command for partially updating the current user's own profile.

    Only fields listed in ``provided_fields`` will be applied.
    For nullable fields (email, phone, birth_date, career) a None value
    combined with
    the field name being present in ``provided_fields`` means "clear this field".
    """
    user_id: str
    provided_fields: frozenset
    name: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    career: Optional[str] = None
    tags: tuple = field(default_factory=tuple)
    avatar_url: Optional[str] = None
    language_skills: tuple = field(default_factory=tuple)
    registered_address: Optional[str] = None
    residential_address: Optional[str] = None
    is_residential_same_as_registered: Optional[bool] = None
    gender: Optional[str] = None


@dataclass(frozen=True)
class ChangePasswordCommand:
    """Command for changing the authenticated user's own password."""
    user_id: str
    current_password: str
    new_password: str


@dataclass(frozen=True)
class AdminUpdateUserCommand:
    """Command for an admin to update any user's profile.

    Only fields listed in ``provided_fields`` will be applied.
    ``password`` is hashed before being set on the entity.
    """
    user_id: str          # target user to update
    admin_id: str         # admin performing the action
    provided_fields: frozenset
    name: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    career: Optional[str] = None
    tags: tuple = field(default_factory=tuple)
    avatar_url: Optional[str] = None
    language_skills: tuple = field(default_factory=tuple)
    registered_address: Optional[str] = None
    residential_address: Optional[str] = None
    is_residential_same_as_registered: Optional[bool] = None
    gender: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    password: Optional[str] = None  # plain text; service hashes it
