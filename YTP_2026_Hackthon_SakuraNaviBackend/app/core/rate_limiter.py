"""In-memory sliding-window rate limiter for brute-force protection.

Stores per-key request timestamps and blocks requests that exceed the
configured threshold within the rolling time window.

.. warning::
    This implementation stores state in process memory.  When the application
    is deployed with multiple workers (e.g. ``uvicorn --workers N`` or
    gunicorn), each worker maintains an independent counter so an attacker can
    bypass per-IP / per-account limits by spreading requests across workers.
    For multi-worker deployments replace this with a shared backend such as
    Redis (e.g. via `fastapi-limiter`).
"""
import asyncio
import ipaddress
import os
import time
from collections import defaultdict

from fastapi import Request

_store: dict[str, list[float]] = defaultdict(list)
_lock = asyncio.Lock()

_TESTING = os.environ.get("APP_ENV") == "test"

LOGIN_IP_MAX = 10        # maximum login attempts per IP per window
LOGIN_IP_WINDOW = 60     # seconds
LOGIN_ACCT_MAX = 5       # maximum failed attempts per account per window
LOGIN_ACCT_WINDOW = 900  # 15 minutes

REFRESH_IP_MAX = 30      # maximum refresh attempts per IP per window
REFRESH_IP_WINDOW = 60   # seconds
REFRESH_ACCT_MAX = 15    # maximum refresh attempts per account per window
REFRESH_ACCT_WINDOW = 60 # seconds

REGISTER_IP_MAX = 10      # maximum register attempts per IP per window
REGISTER_IP_WINDOW = 60   # seconds

# Rate-limit store key prefixes — using constants prevents typo-based key
# collisions across different endpoint throttles.
LOGIN_IP_KEY_PREFIX = "login:ip:"
LOGIN_ACCT_KEY_PREFIX = "login:acct:"
REFRESH_IP_KEY_PREFIX = "refresh:ip:"
REFRESH_ACCT_KEY_PREFIX = "refresh:acct:"
REGISTER_IP_KEY_PREFIX = "register:ip:"


def _is_valid_ip(address: str) -> bool:
    """Return True if *address* is a syntactically valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


def get_client_ip(request: Request) -> str:
    """Resolve the real client IP, honouring X-Forwarded-For only from trusted proxies.

    Only trusts the X-Forwarded-For header when the direct connection comes from
    an IP in settings.trusted_proxies, preventing spoofing by arbitrary clients.
    Falls back to request.client.host when the header is absent or untrusted.
    """
    from app.core.config import settings  # local import avoids circular dependency

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        direct_ip = request.client.host if request.client else None
        if direct_ip in settings.trusted_proxies:
            # Header may contain a comma-separated chain: client, proxy1, proxy2.
            # The leftmost address is the originating client.
            candidate = forwarded_for.split(",")[0].strip()
            if candidate and _is_valid_ip(candidate):
                return candidate
    if request.client:
        return request.client.host
    return "unknown"


def _prune(key: str, now: float, window_seconds: int) -> list[float]:
    """Return timestamps within the window and remove stale entries from the store.

    Also deletes the key entirely when no timestamps remain, preventing
    unbounded memory growth in long-running processes.
    """
    valid = [t for t in _store[key] if now - t < window_seconds]
    if not valid:
        _store.pop(key, None)
    return valid


async def is_allowed(key: str, max_attempts: int, window_seconds: int) -> bool:
    """Check and record an attempt. Return True if the request is allowed."""
    now = time.monotonic()
    async with _lock:
        valid = _prune(key, now, window_seconds)
        if len(valid) >= max_attempts:
            return False
        valid.append(now)
        _store[key] = valid
        return True


async def record_failed(key: str, max_attempts: int, window_seconds: int) -> None:
    """Record a failed attempt (for account-level throttling on failure only)."""
    now = time.monotonic()
    async with _lock:
        valid = _prune(key, now, window_seconds)
        valid.append(now)
        _store[key] = valid


async def record_success(key: str, max_attempts: int, window_seconds: int) -> None:
    """Record a successful attempt and reset the bucket.

    Decrements one failed-attempt record from the bucket, providing a
    "grace" mechanism so transient failures don't permanently lock an account.
    No-op if the bucket is already empty.
    """
    now = time.monotonic()
    async with _lock:
        valid = _prune(key, now, window_seconds)
        if valid:
            valid.pop(0)  # remove oldest entry (one failed attempt absorbed)
        _store[key] = valid


async def is_blocked(key: str, max_attempts: int, window_seconds: int) -> bool:
    """Check if a key is currently blocked (without recording an attempt)."""
    now = time.monotonic()
    async with _lock:
        valid = _prune(key, now, window_seconds)
        return len(valid) >= max_attempts


def reset_key(key: str) -> None:
    """[TEST-ONLY] Clear all timestamps for a single key.

    Do NOT call this in production code — it silently bypasses rate limiting.
    """
    if not _TESTING:
        raise RuntimeError(
            "reset_key() must not be called outside of APP_ENV='test'."
        )
    _store.pop(key, None)


def clear_all() -> None:
    """[TEST-ONLY] Clear all rate-limit state.

    Do NOT call this in production code — it silently bypasses rate limiting.
    """
    if not _TESTING:
        raise RuntimeError(
            "clear_all() must not be called outside of APP_ENV='test'."
        )
    _store.clear()
