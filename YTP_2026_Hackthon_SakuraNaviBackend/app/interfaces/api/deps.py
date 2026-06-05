"""FastAPI dependency injection — provide application services per request."""
from typing import Annotated, Tuple

import httpx
import uuid as _uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.admin.service import AdminApplicationService
from app.application.chat.ports import LLMClient, ToolExecutor
from app.application.chat.query_service import ChatQueryService
from app.application.chat.service import ChatApplicationService
from app.application.rag.frontend_service import RagFrontendApplicationService
from app.application.rag.ports import EmbeddingClient, Tokenizer
from app.application.rag.service import RagApplicationService
from app.application.resume.service import ResumeApplicationService
from app.application.resume_draft.service import ResumeDraftApplicationService
from app.application.user.service import UserApplicationService
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.infrastructure.auth.admin_jwt_service import AdminJwtService
from app.infrastructure.auth.jwt_service import JwtTokenService
from app.infrastructure.auth.password_service import BcryptPasswordHasher
from app.infrastructure.db.session import get_db_session
from app.infrastructure.embeddings.factory import build_embedding_client
from app.infrastructure.llm.minimax_client import MiniMaxClient
from app.infrastructure.llm.gemini_client import GeminiClient
from app.infrastructure.llm.tool_registry import ToolExecutorImpl

from app.infrastructure.rag.classifier import DocumentClassifier
from app.infrastructure.rag.jieba_tokenizer import JiebaTokenizer
from app.infrastructure.repositories.rag_repository import RagRepositoryImpl

from app.infrastructure.repositories.admin_repository import AdminRepositoryImpl

from app.infrastructure.repositories.refresh_token_repository import RefreshTokenRepositoryImpl
from app.infrastructure.repositories.resume_repository import ResumeRepositoryImpl
from app.infrastructure.repositories.resume_draft_repository import ResumeDraftRepositoryImpl
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.infrastructure.repositories.chat_repository import ChatRepositoryImpl
from sqlalchemy.ext.asyncio import AsyncSession

_bearer_scheme = HTTPBearer(auto_error=False)
_jwt_service = JwtTokenService()
_admin_jwt_service = AdminJwtService()
_bcrypt_hasher = BcryptPasswordHasher()

_minimax_client: MiniMaxClient | None = None
_gemini_client: GeminiClient | None = None
_http_client: httpx.AsyncClient | None = None
_embedding_client: EmbeddingClient | None = None
_tokenizer: JiebaTokenizer | None = None
_classifier: "DocumentClassifier | None" = None


def _get_minimax_client() -> MiniMaxClient:
    global _minimax_client
    if _minimax_client is None:
        _minimax_client = MiniMaxClient(
            api_key=settings.minimax_api_key,
            base_url=settings.minimax_base_url,
            model=settings.minimax_model,
            max_tokens=settings.minimax_max_tokens,
            temperature=settings.minimax_temperature,
        )
    return _minimax_client


def _get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient(
            api_key=settings.gemini_api_key,
            base_url=settings.gemini_base_url,
            model=settings.gemini_model,
            max_tokens=settings.gemini_max_tokens,
            temperature=settings.gemini_temperature,
        )
    return _gemini_client


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20, keepalive_expiry=30.0),
        )
    return _http_client


def _get_embedding_client() -> EmbeddingClient:
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = build_embedding_client()
    return _embedding_client


def _get_tokenizer() -> JiebaTokenizer:
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = JiebaTokenizer()
    return _tokenizer


def _get_classifier() -> DocumentClassifier:
    global _classifier
    if _classifier is None:
        from app.infrastructure.rag.classifier import build_classifier
        _classifier = build_classifier()
    return _classifier


async def close_shared_clients() -> None:
    global _http_client, _minimax_client, _gemini_client, _embedding_client
    if _embedding_client is not None:
        # Embedding client shares the global http client; do not double-close.
        _embedding_client = None
    if _minimax_client is not None:
        await _minimax_client.close()
        _minimax_client = None
    if _gemini_client is not None:
        await _gemini_client.close()
        _gemini_client = None
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def get_user_app_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserApplicationService:
    return UserApplicationService(
        user_repo=UserRepositoryImpl(session),
        refresh_token_repo=RefreshTokenRepositoryImpl(session),
        password_hasher=_bcrypt_hasher,
        token_service=_jwt_service,
    )


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return _jwt_service.decode_access_token(credentials.credentials)
    except UnauthorizedException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Tuple[str, str]:
    """Verify the caller is an active admin and return (admin_id, role)."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        admin_id, role = _admin_jwt_service.decode_admin_access_token(credentials.credentials)
    except UnauthorizedException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.domains.admin.value_objects import AdminId
    admin_repo = AdminRepositoryImpl(session)
    admin = await admin_repo.find_by_id(AdminId(_uuid.UUID(admin_id)))
    if admin is None or not admin.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return admin_id, role


async def get_current_admin_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Tuple[str, str] | None:
    """Like get_current_admin but returns None instead of raising for missing/invalid admin creds."""
    if credentials is None:
        return None
    try:
        admin_id, role = _admin_jwt_service.decode_admin_access_token(credentials.credentials)
    except UnauthorizedException:
        return None
    from app.domains.admin.value_objects import AdminId
    admin_repo = AdminRepositoryImpl(session)
    admin = await admin_repo.find_by_id(AdminId(_uuid.UUID(admin_id)))
    if admin is None or not admin.is_active():
        return None
    return admin_id, role


async def get_current_admin_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> str:
    """Verify the caller is an active admin and return their admin_id."""
    admin_id, _ = await get_current_admin(credentials, session)
    return admin_id


def get_current_access_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_rag_app_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RagApplicationService:
    return RagApplicationService(
        rag_repo=RagRepositoryImpl(session),
        embedding_client=_get_embedding_client(),
        tokenizer=_get_tokenizer(),
        classifier=_get_classifier(),
    )


def get_rag_frontend_app_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RagFrontendApplicationService:
    rag_app_service = RagApplicationService(
        rag_repo=RagRepositoryImpl(session),
        embedding_client=_get_embedding_client(),
        tokenizer=_get_tokenizer(),
        classifier=_get_classifier(),
    )
    resume_app_service = ResumeApplicationService(
        resume_repo=ResumeRepositoryImpl(session),
        user_repo=UserRepositoryImpl(session),
    )
    return RagFrontendApplicationService(rag_app_service, resume_app_service)


def get_chat_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_app_service: Annotated[UserApplicationService, Depends(get_user_app_service)],
    access_token: Annotated[str, Depends(get_current_access_token)],
) -> ChatApplicationService:
    resume_app_service = ResumeApplicationService(
        resume_repo=ResumeRepositoryImpl(session),
        user_repo=UserRepositoryImpl(session),
    )
    rag_app_service = RagApplicationService(
        rag_repo=RagRepositoryImpl(session),
        embedding_client=_get_embedding_client(),
        tokenizer=_get_tokenizer(),
        classifier=_get_classifier(),
    )
    resume_draft_app_service = ResumeDraftApplicationService(
        draft_repo=ResumeDraftRepositoryImpl(session),
        resume_service=resume_app_service,
    )
    tool_executor = ToolExecutorImpl(
        user_app_service,
        _get_http_client(),
        access_token,
        resume_app_service,
        rag_app_service,
        resume_draft_app_service=resume_draft_app_service,
    )
    return ChatApplicationService(_get_minimax_client(), tool_executor, ChatRepositoryImpl(session))


def get_chat_query_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChatQueryService:
    return ChatQueryService(chat_repo=ChatRepositoryImpl(session))


def get_resume_app_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResumeApplicationService:
    return ResumeApplicationService(
        resume_repo=ResumeRepositoryImpl(session),
        user_repo=UserRepositoryImpl(session),
    )


def get_admin_app_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminApplicationService:
    return AdminApplicationService(
        admin_repo=AdminRepositoryImpl(session),
        password_hasher=_bcrypt_hasher,
        jwt_service=_admin_jwt_service,
    )