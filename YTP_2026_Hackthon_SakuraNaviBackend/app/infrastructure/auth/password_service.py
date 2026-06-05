"""bcrypt password hashing service — implements PasswordHasher port."""
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)

# Computed once at module load.  Used to normalise response time for
# non-existent accounts during login, preventing timing-based enumeration.
_DUMMY_BCRYPT_HASH: str = _pwd_context.hash("__dummy_constant_timing__")


class BcryptPasswordHasher:
    # Expose the dummy hash via an instance attribute so callers that only
    # hold a PasswordHasher protocol reference can access it without an
    # infrastructure import.
    dummy_hash: str = _DUMMY_BCRYPT_HASH

    def hash(self, password: str) -> str:
        return _pwd_context.hash(password)

    def verify(self, plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)
