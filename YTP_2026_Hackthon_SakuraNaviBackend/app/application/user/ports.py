"""Protocol interfaces (ports) for external services — enables dependency inversion."""
from datetime import datetime
from typing import Optional, Protocol


class PasswordHasher(Protocol):
    """Port for password hashing operations."""
    dummy_hash: str  # Pre-computed hash used for constant-time login responses.

    def hash(self, password: str) -> str: ...
    def verify(self, plain: str, hashed: str) -> bool: ...


class TokenService(Protocol):
    """Port for JWT token operations."""

    def create_access_token(self, user_id: str, role: str = "user") -> str: ...
    def create_refresh_token(self, user_id: str) -> tuple[str, str]:
        """Returns (raw_token, jti)."""
        ...
    def decode_access_token(self, token: str) -> str:
        """Returns user_id. Raises UnauthorizedException on invalid token."""
        ...
    def decode_refresh_token(self, token: str) -> tuple[str, str]:
        """Returns (user_id, jti). Raises UnauthorizedException on invalid token."""
        ...


class RefreshTokenRepository(Protocol):
    """Port for refresh token persistence operations."""

    async def save(self, jti: str, user_id: str, expires_at: datetime, family_id: str) -> None: ...
    async def exists_and_valid(self, jti: str) -> bool: ...
    async def revoke(self, jti: str) -> None: ...
    async def revoke_all_for_user(self, user_id: str) -> None: ...
    async def find_family_id_by_jti(self, jti: str) -> Optional[str]:
        """Return the family_id for a given jti, or None if not found."""
        ...
    async def revoke_family(self, family_id: str) -> None:
        """Revoke all tokens belonging to a family (theft-detection response)."""
        ...
