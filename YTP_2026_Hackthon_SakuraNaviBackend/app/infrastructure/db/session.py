"""Async database session factory."""
from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.exceptions import DuplicateResourceException

engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionFactory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            # Always commit: ORM-level changes (session.new/dirty/deleted) AND Core SQL
            # bulk statements (execute(delete(...))) all need a commit to persist.
            # The previous read-only skip based on session.new/dirty/deleted was incorrect —
            # Core SQL DML bypasses ORM unit-of-work tracking, causing bulk deletes to
            # silently roll back. SQLAlchemy autobegin means commit() is a no-op when
            # no database activity occurred, so this is safe for read-only paths.
            await session.commit()
            logger.debug("DB transaction committed")
        except IntegrityError as exc:
            await session.rollback()
            logger.debug("DB IntegrityError — unique constraint violated: {}", exc)
            raise DuplicateResourceException(
                "A unique constraint was violated.",
                code="DUPLICATE_RESOURCE",
            ) from exc
        except Exception as exc:
            await session.rollback()
            logger.debug("DB session rollback — {}: {}", type(exc).__name__, exc)
            raise
