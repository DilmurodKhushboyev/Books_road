"""Baza ulanishi: engine va sessiya fabrikasi (yagona eshik)."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str) -> AsyncEngine:
    global _engine, _session_factory
    kwargs: dict = {"pool_pre_ping": True}
    if not database_url.startswith("sqlite"):
        kwargs.update(pool_size=10, max_overflow=20)
    _engine = create_async_engine(database_url, **kwargs)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def set_session_factory(factory: async_sessionmaker[AsyncSession]) -> None:
    """Testlar uchun: tayyor fabrikani o'rnatish."""
    global _session_factory
    _session_factory = factory


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Tranzaksiya: xato bo'lsa rollback, aks holda commit."""
    if _session_factory is None:
        raise RuntimeError("Baza ishga tushirilmagan: init_engine() chaqirilmagan")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    if _engine is not None:
        await _engine.dispose()
