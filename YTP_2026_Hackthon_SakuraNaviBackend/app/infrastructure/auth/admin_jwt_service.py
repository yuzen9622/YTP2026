"""JWT token service for admin authentication — separate from user JWT."""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

_ADMIN_ACCESS_TOKEN_TYPE = "admin_access"


def _jwt_algorithm() -> str:
    return settings.algorithm


class AdminJwtService:
    """JWT service for admin tokens — payload includes admin_id and role."""

    def create_admin_access_token(self, admin_id: str, role: str) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": admin_id,
            "iss": settings.jwt_issuer,
            "type": _ADMIN_ACCESS_TOKEN_TYPE,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=_jwt_algorithm())

    def decode_admin_access_token(self, token: str) -> tuple[str, str]:
        """Decode admin token and return (admin_id, role). Raises on error."""
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[_jwt_algorithm()],
                issuer=settings.jwt_issuer,
            )
        except JWTError:
            raise UnauthorizedException(
                "Could not validate admin access token.", code="INVALID_ADMIN_ACCESS_TOKEN"
            )

        if payload.get("type") != _ADMIN_ACCESS_TOKEN_TYPE:
            raise UnauthorizedException(
                "Wrong token type for admin.", code="WRONG_TOKEN_TYPE"
            )

        admin_id: str | None = payload.get("sub")
        if admin_id is None:
            raise UnauthorizedException(
                "Token missing subject.", code="INVALID_ADMIN_ACCESS_TOKEN"
            )
        role: str = payload.get("role", "admin")
        return admin_id, role