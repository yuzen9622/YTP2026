"""FastAPI application factory."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    ApplicationException,
    DuplicateResourceException,
    ForbiddenException,
    ResourceNotFoundException,
    UnauthorizedException,
)
from app.domains.domain_exceptions import DomainException
from app.interfaces.api.v1.router import api_v1_router
from loguru import logger

_CORS_ALLOW_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Manage application-level resource lifecycle."""
    from app.infrastructure.scheduler import start_scheduler, stop_scheduler

    await start_scheduler()
    yield
    await stop_scheduler()
    from app.interfaces.api.deps import close_shared_clients

    await close_shared_clients()


def create_app() -> FastAPI:
    from app.infrastructure.logging import setup_logging  # noqa: PLC0415
    setup_logging()

    app = FastAPI(
        title="SakuraNavi Backend",
        version="0.2.0",
        lifespan=_lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        # Disable built-in /openapi.json in production to avoid exposing API structure.
        # A custom handler below re-adds it for non-prod with Cache-Control headers.
        openapi_url="/openapi.json" if settings.app_env != "production" else None,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=list(_CORS_ALLOW_METHODS),
        allow_headers=["Authorization", "Content-Type", "Accept"],
        expose_headers=["Retry-After"],
    )

    # ── Strip Server header to avoid version fingerprinting ──────────────────
    @app.middleware("http")
    async def remove_server_header(request: Request, call_next) -> Response:
        response = await call_next(request)
        if "server" in response.headers:
            del response.headers["server"]
        return response

    app.include_router(api_v1_router)

    # --- exception handlers ---

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message, "code": exc.code},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ForbiddenException)
    async def forbidden_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(ResourceNotFoundException)
    async def not_found_handler(
        request: Request, exc: ResourceNotFoundException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(DuplicateResourceException)
    async def conflict_handler(
        request: Request, exc: DuplicateResourceException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(ApplicationException)
    async def application_exception_handler(
        request: Request, exc: ApplicationException
    ) -> JSONResponse:
        # Log the real detail for debugging but do not expose it to the client
        # to prevent leaking system paths, query text, or internal state.
        logger.error("Unhandled ApplicationException [{}]: {}", exc.code, exc.message)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred.", "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on {} {}", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred.", "code": "INTERNAL_ERROR"},
        )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        return {"status": "ok"}

    # Serve /openapi.json only in non-production environments, with
    # Cache-Control: no-store to prevent stale schema in ReDoc/Swagger.
    # In production this endpoint does not exist, so API structure is not exposed.
    if settings.app_env != "production":
        @app.get("/openapi.json", include_in_schema=False)
        async def get_openapi_schema() -> JSONResponse:
            return JSONResponse(
                content=app.openapi(),
                headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
            )

    return app


app = create_app()
