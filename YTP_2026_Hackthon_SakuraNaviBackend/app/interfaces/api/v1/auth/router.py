"""Auth API router — register, login, refresh."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError as _JWTError
from jose import jwt as _jose_jwt
from loguru import logger

from app.application.user.commands import (
    LoginCommand,
    RefreshTokenCommand,
    RegisterUserCommand,
)
from app.application.user.service import UserApplicationService
from app.core import rate_limiter
from app.core.exceptions import (
    DuplicateResourceException,
    UnauthorizedException,
)
from app.core.rate_limiter import get_client_ip
from app.interfaces.api.deps import get_admin_app_service, get_user_app_service
from app.interfaces.api.v1.auth.schemas import (
    AdminLoginRequest,
    AdminTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.interfaces.api.v1.users.schemas import UserProfileResponse

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Admin authentication ───────────────────────────────────────────────────────


@router.post(
    "/admin/login",
    response_model=AdminTokenResponse,
    summary="管理者登入",
    description="使用帳號與密碼登入管理者後台，成功後返回 JWT `access_token`。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "帳號或密碼錯誤",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid account or password.", "code": "INVALID_ADMIN_CREDENTIALS"}
                }
            },
        },
    },
)
async def admin_login(
    body: AdminLoginRequest,
    admin_svc: Annotated["AdminApplicationService", Depends(get_admin_app_service)],
) -> AdminTokenResponse:
    from app.application.admin.commands import AuthenticateAdminCommand

    try:
        result = await admin_svc.authenticate_admin(
            AuthenticateAdminCommand(account=body.account, password=body.password)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid account or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AdminTokenResponse(access_token=result.access_token)


def _extract_sub_unverified(token: str) -> Optional[str]:
    """Return the 'sub' claim from a JWT without verifying the signature.

    Used solely for rate-limit key construction — NOT for authentication.
    Using unverified claims here is intentional: we only need a stable
    per-user bucket identifier; the actual service call still validates
    the full token.
    """
    try:
        return _jose_jwt.get_unverified_claims(token).get("sub")
    except _JWTError:
        return None


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="註冊新使用者",
    description=(
        "建立新使用者帳號。\n\n"
        "**Password 規則**：至少 8 個字元，需含大小寫英文字母與數字。\n\n"
        "**電話格式**：含國碼，例如 `+886912345678`。\n\n"
        "**career 可用値**：`unemployed`（待業）、`employed`（在職）、`student`（學生）\n\n"
        "**tags 規則**：最多 20 筆，每筆最多 50 字元。"
    ),
    responses={
        status.HTTP_201_CREATED: {
            "description": "註冊成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "櫻花太郎",
                        "account": "sakura_taro",
                        "email": "sakura@example.com",
                        "phone": "+886912345678",
                        "bio": "這位使用者尚未填寫個人簡介。",
                        "birth_date": "2000-01-15",
                        "career": "employed",
                        "tags": ["旅遊", "美食", "科技"],
                        "is_active": True,
                        "created_at": "2026-04-20T00:00:00+00:00",
                        "updated_at": "2026-04-20T00:00:00+00:00"
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "帳號或 Email 已存在",
            "content": {
                "application/json": {
                    "example": {"detail": "Account already exists", "code": "DUPLICATE_RESOURCE"}
                }
            },
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "註冊請求過於頻繁（Rate Limited）",
            "content": {
                "application/json": {
                    "example": {"detail": "註冊請求過於頻繁，請稍後再試。"}
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "輸入資料格式不正確",
            "content": {
                "application/json": {
                    "example": {"detail": "密碼必須包含至少一個大寫字母"}
                }
            },
        },
    },
)
async def register(
    request: Request,
    body: RegisterRequest,
    svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
) -> UserProfileResponse:
    client_ip = get_client_ip(request)
    ip_key = f"{rate_limiter.REGISTER_IP_KEY_PREFIX}{client_ip}"
    if not await rate_limiter.is_allowed(
        ip_key, rate_limiter.REGISTER_IP_MAX, rate_limiter.REGISTER_IP_WINDOW
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="註冊請求過於頻繁，請稍後再試。",
            headers={"Retry-After": str(rate_limiter.REGISTER_IP_WINDOW)},
        )

    logger.info("[api] POST /auth/register: account={}", body.account)
    try:
        dto = await svc.register(
            RegisterUserCommand(
                name=body.name,
                account=body.account,
                password=body.password,
                email=body.email,
                phone=body.phone,
                birth_date=body.birth_date,
                career=body.career,
                tags=tuple(body.tags) if body.tags else (),
                gender=body.gender,
            )
        )
    except DuplicateResourceException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=exc.message
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    return UserProfileResponse(**dto.__dict__)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="使用者登入",
    description=(
        "使用帳號與密碼登入，成功後返回 JWT `access_token`（短效）與 `refresh_token`（長效）。\n\n"
        "**速率限制**：同一 IP 每 60 秒最多 10 次；\n"
        "登入失敗累積次數過多將暫時鎖定帳號。"
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "帳號或密碼錯誤",
            "content": {
                "application/json": {
                    "example": {"detail": "帳號或密碼錯誤", "code": "UNAUTHORIZED"}
                }
            },
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "請求過於頻繁（Rate Limited）",
            "content": {
                "application/json": {
                    "example": {"detail": "登入請求過於頻繁，請稍後再試。"}
                }
            },
        },
    },
)
async def login(
    request: Request,
    body: LoginRequest,
    svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
) -> TokenResponse:
    logger.info("[api] POST /auth/login: account={}", body.account)
    client_ip = get_client_ip(request)
    ip_key = f"{rate_limiter.LOGIN_IP_KEY_PREFIX}{client_ip}"
    acct_key = f"{rate_limiter.LOGIN_ACCT_KEY_PREFIX}{body.account}"

    # Layer-1: IP-based rate limit (10 requests / 60 s)
    if not await rate_limiter.is_allowed(
        ip_key, rate_limiter.LOGIN_IP_MAX, rate_limiter.LOGIN_IP_WINDOW
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登入請求過於頻繁，請稍後再試。",
            headers={"Retry-After": str(rate_limiter.LOGIN_IP_WINDOW)},
        )

    # Layer-2: account-based block check (recorded only on failure)
    if await rate_limiter.is_blocked(
        acct_key, rate_limiter.LOGIN_ACCT_MAX, rate_limiter.LOGIN_ACCT_WINDOW
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="This account is temporarily locked. Please try again later.",
            headers={"Retry-After": str(rate_limiter.LOGIN_ACCT_WINDOW)},
        )

    try:
        dto = await svc.login(LoginCommand(account=body.account, password=body.password))
    except UnauthorizedException as exc:
        # Only record a failed attempt for bad credentials.
        # Account-inactive errors should NOT increment the counter — an attacker
        # could otherwise deliberately lock out deactivated (or valid) accounts.
        if exc.code == "INVALID_CREDENTIALS":
            await rate_limiter.record_failed(
                acct_key, rate_limiter.LOGIN_ACCT_MAX, rate_limiter.LOGIN_ACCT_WINDOW
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Absorb one prior failure record so transient mistakes don't permanently
    # lock the account (mirrors the same grace mechanism in /refresh).
    await rate_limiter.record_success(
        acct_key, rate_limiter.LOGIN_ACCT_MAX, rate_limiter.LOGIN_ACCT_WINDOW
    )
    return TokenResponse(**dto.__dict__)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新 Token",
    description=(
        "使用有效的 `refresh_token` 取得新的 `access_token` 與 `refresh_token`（Token Rotation 機制）。\n\n"
        "> 每次刷新成功後，原 `refresh_token` 即失效。\n\n"
        "**同一 Token Family 的所有舊 token 也會同時被撤銷**（盜用偵測機制）："
        "若有任何舊 refresh_token 被偵測到已使用，該 family 的**所有** session 都會被撤銷。\n\n"
        "**速率限制**：同一 IP 每 60 秒最多 30 次；同一帳號每 60 秒最多 15 次。"
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "刷新成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access.signature",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh.signature",
                        "token_type": "bearer"
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Refresh token 無效或已過期",
            "content": {
                "application/json": {
                    "example": {"detail": "Refresh Token 無效或已過期", "code": "UNAUTHORIZED"}
                }
            },
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "請求過於頻繁（Rate Limited）",
            "content": {
                "application/json": {
                    "example": {"detail": "刷新次數過於頻繁，請稍後再試。"}
                }
            },
        },
    },
)
async def refresh(
    request: Request,
    body: RefreshRequest,
    svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
) -> TokenResponse:
    client_ip = get_client_ip(request)
    ip_key = f"{rate_limiter.REFRESH_IP_KEY_PREFIX}{client_ip}"

    if not await rate_limiter.is_allowed(
        ip_key, rate_limiter.REFRESH_IP_MAX, rate_limiter.REFRESH_IP_WINDOW
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="刷新次數過於頻繁，請稍後再試。",
            headers={"Retry-After": str(rate_limiter.REFRESH_IP_WINDOW)},
        )

    # Per-account rate limit: derive the bucket key from unverified claims, but
    # perform only a READ (is_blocked) check here.  We write to the bucket ONLY
    # after the service call succeeds — meaning the claim was fully verified by
    # signature + DB lookup.  A forged 'sub' can trigger a read check but cannot
    # inject entries into a victim's bucket, eliminating the DoS vector.
    user_id_claim = _extract_sub_unverified(body.refresh_token)
    logger.debug("[api] POST /auth/refresh: sub_claim={}", user_id_claim)
    acct_key = (
        f"{rate_limiter.REFRESH_ACCT_KEY_PREFIX}{user_id_claim}"
        if user_id_claim
        else None
    )
    if acct_key and await rate_limiter.is_blocked(
        acct_key, rate_limiter.REFRESH_ACCT_MAX, rate_limiter.REFRESH_ACCT_WINDOW
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="刷新次數過於頻繁，請稍後再試。",
            headers={"Retry-After": str(rate_limiter.REFRESH_ACCT_WINDOW)},
        )

    try:
        dto = await svc.refresh(RefreshTokenCommand(refresh_token=body.refresh_token))
    except UnauthorizedException as exc:
        # Write to the account-level bucket ONLY when the JWT signature was
        # successfully verified (i.e. the 'sub' claim is trustworthy).
        #
        # Whitelist of codes produced AFTER signature verification:
        #   "REFRESH_TOKEN_NOT_FOUND"  — signature OK, token absent from DB
        #   "TOKEN_REUSE_DETECTED"     — signature OK, replay attack detected
        #
        # Any other code (e.g. "INVALID_REFRESH_TOKEN" from a bad/forged
        # signature) means sub is unverified — writing to the account bucket
        # would allow an attacker to lock any account by forging the sub (DoS).
        if acct_key and exc.code in ("REFRESH_TOKEN_NOT_FOUND", "TOKEN_REUSE_DETECTED"):
            await rate_limiter.record_failed(
                acct_key, rate_limiter.REFRESH_ACCT_MAX, rate_limiter.REFRESH_ACCT_WINDOW
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Record successful refresh to absorb one prior failure from the bucket.
    # This provides a "grace" mechanism so transient failures don't permanently
    # lock an account.  The sub claim is now implicitly verified.
    if acct_key:
        await rate_limiter.record_success(
            acct_key, rate_limiter.REFRESH_ACCT_MAX, rate_limiter.REFRESH_ACCT_WINDOW
        )

    return TokenResponse(**dto.__dict__)
