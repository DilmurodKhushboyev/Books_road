"""Umumiy fixture'lar: vaqtinchalik SQLite baza, soxta AI, test rasm."""
import io
import os

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("BOT_TOKEN", "")
os.environ.setdefault("GEMINI_API_KEY", "")

from app.ai.base import DetectedItem, MatchChoice  # noqa: E402
from app.constants import ROLE_STAFF  # noqa: E402
from app.db import session as db_session  # noqa: E402
from app.db.models import Base  # noqa: E402
from app.repositories import user_repo  # noqa: E402
from app.services.access_service import resolve_context  # noqa: E402
from app.services.layout_service import ensure_default_store  # noqa: E402


@pytest.fixture
async def db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    db_session.set_session_factory(factory)
    async with db_session.session_scope() as session:
        await ensure_default_store(session)
    yield factory
    await engine.dispose()


async def make_ctx(telegram_id: int, staff: bool = False, admin_ids: frozenset[int] = frozenset()):
    async with db_session.session_scope() as session:
        ctx = await resolve_context(session, telegram_id, f"User {telegram_id}", None, admin_ids)
        if staff:
            await user_repo.set_role(session, ctx.store_id, ctx.user_id, ROLE_STAFF)
    async with db_session.session_scope() as session:
        return await resolve_context(session, telegram_id, f"User {telegram_id}", None, admin_ids)


@pytest.fixture
def photo_bytes() -> bytes:
    image = Image.new("RGB", (400, 300), (20, 40, 160))
    for x in range(200, 400):
        for y in range(0, 300, 3):
            image.putpixel((x, y), (220, 30, 30))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


class FakeAI:
    """Oldindan berilgan natijalarni qaytaradigan AI (tarmoqsiz testlar uchun)."""

    def __init__(self, detected=None, described=None, choice=None):
        self.detected = detected or []
        self.described = described
        self.choice = choice or MatchChoice(index=None, confidence=0.0)
        self.calls: list[str] = []

    async def detect_items(self, image: bytes):
        self.calls.append("detect")
        return list(self.detected)

    async def describe_item(self, image: bytes):
        self.calls.append("describe")
        return self.described

    async def choose_match(self, image: bytes, candidates: list[dict]):
        self.calls.append("choose")
        return self.choice


def detected(title, author="", conf=0.9, qty=1, colors=None, kind="book", box=None):
    return DetectedItem(title=title, author=author, kind=kind, colors=colors or ["ko'k"],
                        visual_description="ko'k muqova", quantity=qty, confidence=conf, box=box)
