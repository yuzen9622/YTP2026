"""Application settings: all sensitive values MUST come from .env/environment."""

import os
from pathlib import Path

from dotenv import dotenv_values

_ROOT = Path(__file__).resolve().parents[2]

# Priority: APP_ENV env-var → .env.{APP_ENV} → .env (fallback)
_APP_ENV = os.environ.get("APP_ENV", "development")
_ENV_FILE = _ROOT / f".env.{_APP_ENV}"
if not _ENV_FILE.exists():
    _ENV_FILE = _ROOT / ".env"
_ENV = dotenv_values(_ENV_FILE)

_SECRET_KEY_MIN_LENGTH = 32  # 256 bits minimum for HMAC-SHA256
_ALLOWED_ALGORITHMS = {"HS256", "HS384", "HS512"}  # safe symmetric algorithms only


def _require_env(key: str) -> str:
    """Return the value of a variable from the loaded .env file or os.environ; raise if not set."""
    value = _ENV.get(key) or os.environ.get(key)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{key}' is not set in {_ENV_FILE.name} "
            "or the process environment."
        )
    return value


def _opt_env(key: str, default: str = "") -> str:
    """Return an optional value from the loaded .env file or os.environ."""
    val = _ENV.get(key)
    if val is not None:
        return val
    val = os.environ.get(key)
    if val is not None:
        return val
    return default


class Settings:
    # ── App ──────────────────────────────────────────────────────────────────
    app_env: str = _APP_ENV
    # debug is forced to False in production regardless of env-var to prevent
    # accidental information disclosure if the environment is misconfigured.
    debug: bool = (
        False
        if _APP_ENV == "production"
        else _opt_env("DEBUG", "false").lower() == "true"
    )
    port: int = int(_opt_env("PORT", "8000"))
    log_dir_base: str = _opt_env("LOG_DIR_BASE", "logs")

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = _require_env("DATABASE_URL")

    # ── Auth ─────────────────────────────────────────────────────────────────
    secret_key: str = _require_env("SECRET_KEY")
    algorithm: str = "HS256"
    # JWT issuer claim ('iss') — validated on every token decode to prevent cross-service token reuse.
    jwt_issuer: str = _opt_env("JWT_ISSUER", "sakuranavi")
    access_token_expire_minutes: int = int(
        _opt_env("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    )
    refresh_token_expire_days: int = int(_opt_env("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    bcrypt_rounds: int = int(_opt_env("BCRYPT_ROUNDS", "12"))

    # ── Phone encryption ─────────────────────────────────────────────────────
    phone_encryption_key: str = _require_env("PHONE_ENCRYPTION_KEY")
    phone_hmac_key: str = _require_env("PHONE_HMAC_KEY")

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # Dev default: common local front-end ports.
    # Production: must be explicit — no wildcards allowed with credentials.
    cors_origins: list[str] = [
        o.strip()
        for o in _opt_env(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000",
        ).split(",")
        if o.strip()
    ]
    cors_allow_credentials: bool = (
        _opt_env("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    )

    # ── Trusted Proxies ───────────────────────────────────────────────────────
    # Comma-separated list of proxy IP addresses whose X-Forwarded-For header
    # should be trusted for real-client-IP resolution.
    # Default: loopback only (suitable for local dev / single-host deploy).
    # In production behind an LB/Nginx, set to the actual proxy IP(s).
    trusted_proxies: list[str] = [
        ip.strip()
        for ip in _opt_env("TRUSTED_PROXIES", "127.0.0.1,::1").split(",")
        if ip.strip()
    ]

    # ── Local RAG Embeddings (HuggingFace) ───────────────────────────────────
    rag_local_embedding_model: str = _opt_env(
        "RAG_LOCAL_EMBEDDING_MODEL", "intfloat/multilingual-e5-base"
    )
    # auto/cpu/cuda
    rag_local_embedding_device: str = _opt_env("RAG_LOCAL_EMBEDDING_DEVICE", "auto")
    rag_local_embedding_dimension: int = int(
        _opt_env("RAG_LOCAL_EMBEDDING_DIMENSION", "768")
    )
    rag_local_embedding_max_length: int = int(
        _opt_env("RAG_LOCAL_EMBEDDING_MAX_LENGTH", "512")
    )
    rag_local_embedding_batch_size: int = int(
        _opt_env("RAG_LOCAL_EMBEDDING_BATCH_SIZE", "16")
    )
    rag_local_embedding_local_files_only: bool = (
        _opt_env("RAG_LOCAL_EMBEDDING_LOCAL_FILES_ONLY", "false").lower() == "true"
    )

    # ── MiniMax LLM ───────────────────────────────────────────────────────────
    minimax_api_key: str = _require_env("MINIMAX_API_KEY")
    minimax_base_url: str = _opt_env("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    minimax_model: str = _opt_env("MINIMAX_MODEL", "MiniMax-Text-01")
    minimax_max_tokens: int = int(_opt_env("MINIMAX_MAX_TOKENS", "4096"))
    minimax_temperature: float = float(_opt_env("MINIMAX_TEMPERATURE", "0.7"))

    # ── Gemini LLM ─────────────────────────────────────────────────────────
    gemini_api_key: str = _require_env("GEMINI_API_KEY")
    gemini_base_url: str = _opt_env(
        "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    gemini_model: str = _opt_env("GEMINI_MODEL", "gemini-2.0-flash")
    gemini_max_tokens: int = int(_opt_env("GEMINI_MAX_TOKENS", "4096"))
    gemini_temperature: float = float(_opt_env("GEMINI_TEMPERATURE", "0.7"))

    # ── Tavily Web Search ─────────────────────────────────────────────────────
    tavily_api_key: str = _opt_env("TAVILY_API_KEY", "")
    tavily_base_url: str = _opt_env("TAVILY_BASE_URL", "https://api.tavily.com")
    tavily_search_depth: str = _opt_env("TAVILY_SEARCH_DEPTH", "basic")
    tavily_max_results: int = int(_opt_env("TAVILY_MAX_RESULTS", "5"))

    def __init__(self) -> None:
        if self.rag_local_embedding_dimension != 768:
            raise RuntimeError(
                "RAG_LOCAL_EMBEDDING_DIMENSION must be 768 to match current pgvector schema "
                f"(got {self.rag_local_embedding_dimension})."
            )
        if self.rag_local_embedding_max_length <= 0:
            raise RuntimeError("RAG_LOCAL_EMBEDDING_MAX_LENGTH must be > 0.")
        if self.rag_local_embedding_batch_size <= 0:
            raise RuntimeError("RAG_LOCAL_EMBEDDING_BATCH_SIZE must be > 0.")
        if len(self.secret_key) < _SECRET_KEY_MIN_LENGTH:
            raise RuntimeError(
                f"SECRET_KEY must be at least {_SECRET_KEY_MIN_LENGTH} characters long "
                f"(got {len(self.secret_key)}). Use a cryptographically random value."
            )
        if self.algorithm not in _ALLOWED_ALGORITHMS:
            raise RuntimeError(
                f"algorithm must be one of {sorted(_ALLOWED_ALGORITHMS)} "
                f"(got '{self.algorithm}'). Asymmetric / 'none' algorithms are disallowed."
            )
        if len(self.phone_hmac_key) != 64:
            raise RuntimeError(
                "PHONE_HMAC_KEY must be a 64-character hex string (32 bytes). "
                f"Got {len(self.phone_hmac_key)} characters."
            )
        if self.app_env == "production" and not self.cors_origins:
            raise RuntimeError(
                "CORS_ORIGINS must be explicitly set in production. "
                "Remove the wildcard and set the real front-end domain."
            )


settings = Settings()
