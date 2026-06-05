"""JWT token service — implements TokenService port using python-jose."""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


def _jwt_algorithm() -> str:
    """Return the current JWT algorithm from settings.

    settings.algorithm is validated at startup to be in the symmetric-only
    allowlist, preventing algorithm-confusion attacks.
    """
    return settings.algorithm


class JwtTokenService:
    def create_access_token(self, user_id: str, role: str = "user") -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": user_id,
            "iss": settings.jwt_issuer,
            "type": _ACCESS_TOKEN_TYPE,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=_jwt_algorithm())

    def create_refresh_token(self, user_id: str) -> tuple[str, str]:
        jti = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": user_id,
            "jti": jti,
            "iss": settings.jwt_issuer,
            "type": _REFRESH_TOKEN_TYPE,
            "iat": now,
            "exp": now + timedelta(days=settings.refresh_token_expire_days),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=_jwt_algorithm())
        return token, jti

    def decode_access_token(self, token: str) -> str:
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[_jwt_algorithm()],
                issuer=settings.jwt_issuer,
            )
        except JWTError:
            raise UnauthorizedException(
                "Could not validate access token.", code="INVALID_ACCESS_TOKEN"
            )

        if payload.get("type") != _ACCESS_TOKEN_TYPE:
            raise UnauthorizedException(
                "Wrong token type.", code="WRONG_TOKEN_TYPE"
            )

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(
                "Token missing subject.", code="INVALID_ACCESS_TOKEN"
            )
        return user_id

    def decode_access_token_with_role(self, token: str) -> tuple[str, str]:
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[_jwt_algorithm()],
                issuer=settings.jwt_issuer,
            )
        except JWTError:
            raise UnauthorizedException(
                "Could not validate access token.", code="INVALID_ACCESS_TOKEN"
            )

        if payload.get("type") != _ACCESS_TOKEN_TYPE:
            raise UnauthorizedException(
                "Wrong token type.", code="WRONG_TOKEN_TYPE"
            )

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(
                "Token missing subject.", code="INVALID_ACCESS_TOKEN"
            )
        role: str = payload.get("role", "user")
        return user_id, role

    def decode_refresh_token(self, token: str) -> tuple[str, str]:
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[_jwt_algorithm()],
                issuer=settings.jwt_issuer,
            )
        except JWTError:
            raise UnauthorizedException(
                "Could not validate refresh token.", code="INVALID_REFRESH_TOKEN"
            )

        if payload.get("type") != _REFRESH_TOKEN_TYPE:
            raise UnauthorizedException(
                "Wrong token type.", code="WRONG_TOKEN_TYPE"
            )

        user_id: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if not user_id or not jti:
            raise UnauthorizedException(
                "Invalid refresh token payload.", code="INVALID_REFRESH_TOKEN"
            )
        return user_id, jti
