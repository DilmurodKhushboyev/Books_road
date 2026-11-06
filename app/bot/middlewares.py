"""Bot middleware'lari: foydalanuvchi konteksti va rate limit (har bir update uchun)."""
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from app.db.session import session_scope
from app.services.access_service import resolve_context
from app.services.rate_limit import general_limiter
from app.texts import error_text

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        user: User | None = data.get("event_from_user")
        if user and not general_limiter.allow(user.id):
            logger.info("rate limit: user=%s", user.id)
            if isinstance(event, CallbackQuery):
                await event.answer(error_text("rate_limited"), show_alert=True)
            elif isinstance(event, Message):
                await event.answer(error_text("rate_limited"))
            return None
        return await handler(event, data)


class ContextMiddleware(BaseMiddleware):
    """Har bir update'da `ctx: UserContext` ni handlerga beradi."""

    def __init__(self, admin_ids: frozenset[int]) -> None:
        self._admin_ids = admin_ids

    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None or user.is_bot:
            return None
        async with session_scope() as session:
            ctx = await resolve_context(session, user.id, user.full_name, user.username, self._admin_ids)
        if ctx.is_blocked:
            return None
        data["ctx"] = ctx
        return await handler(event, data)
