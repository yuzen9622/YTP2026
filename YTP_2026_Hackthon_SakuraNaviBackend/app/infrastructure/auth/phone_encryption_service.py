"""Phone number encryption service.

Design
------
- **Storage (Fernet)**: AES-128-CBC + HMAC-SHA256 with a random IV per call.
  Provides confidentiality and integrity for the phone number at rest.
  Ciphertext is non-deterministic, so the same number produces a different
  value each time it is encrypted.

- **Lookup (HMAC-SHA256)**: A separate deterministic HMAC computed over the
  normalised E.164 phone number using an independent key.  The digest is
  stored in a dedicated ``phone_hmac`` column so that uniqueness checks and
  searches can be performed without decrypting all rows.

Both keys must be supplied via environment variables:
  PHONE_ENCRYPTION_KEY  — URL-safe base64-encoded 32-byte Fernet key
  PHONE_HMAC_KEY        — 64-character hex string (32 bytes)
"""
import hashlib
import hmac as _hmac

from cryptography.fernet import Fernet

from app.core.config import settings


class PhoneEncryptionService:
    def __init__(self, encryption_key: str, hmac_key: str) -> None:
        self._fernet = Fernet(encryption_key.encode())
        self._hmac_key = bytes.fromhex(hmac_key)

    def encrypt(self, phone: str) -> str:
        """Return the Fernet-encrypted ciphertext of a normalised phone number."""
        return self._fernet.encrypt(phone.encode("utf-8")).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a Fernet ciphertext back to the original phone number."""
        return self._fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")

    def compute_hmac(self, phone: str) -> str:
        """Return the hex-encoded HMAC-SHA256 digest of a normalised phone number."""
        return _hmac.new(
            self._hmac_key, phone.encode("utf-8"), hashlib.sha256
        ).hexdigest()


# Module-level singleton — initialised once from application settings.
phone_encryption_service = PhoneEncryptionService(
    encryption_key=settings.phone_encryption_key,
    hmac_key=settings.phone_hmac_key,
)
