"""Bot va Dispatcher yig'ish: routerlar tartibi, middleware'lar, bog'liqliklar."""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.ai.base import AIProvider
from app.bot.handlers import add_items, browse, errors, find_photo, search, start
from app.bot.middlewares import ContextMiddleware, RateLimitMiddleware
from app.config import Settings


def build_dispatcher(settings: Settings, ai: AIProvider) -> Dispatcher:
    # MemoryStorage faqat ID larni saqlaydi; bir nechta instansda RedisStorage'ga almashtiriladi.
    dp = Dispatcher(storage=MemoryStorage())
    dp["settings"] = settings
    dp["ai"] = ai
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(RateLimitMiddleware())
        observer.outer_middleware(ContextMiddleware(settings.admin_ids))
    # Tartib muhim: aniq tugmalar/holatlar avval, umumiy matn qidiruvi eng oxirida.
    dp.include_routers(*(module.build_router() for module in (
        errors, start, browse, add_items, find_photo, search,
    )))
    return dp


def build_bot(settings: Settings) -> Bot:
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
