from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_engine = None
_async_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.database_url, echo=False)
    return _engine


def get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        # avoid using an annotated assignment to a global name inside the function
        _async_session_factory = async_sessionmaker(
            get_engine(), expire_on_commit=False
        )
    return _async_session_factory


async def get_db() -> AsyncSession:  # pyright: ignore[reportInvalidTypeForm]
    async with get_session_factory()() as session:
        yield session  # pyright: ignore[reportReturnType]
