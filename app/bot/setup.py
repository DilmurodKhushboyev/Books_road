"""Bot va Dispatcher yig'ish: routerlar tartibi, middleware'lar, bog'liqliklar."""
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.ai.base import AIProvider
from app.bot import texts
from app.bot.handlers import add_items, browse, errors, find_photo, search, start
from app.bot.middlewares import ContextMiddleware, RateLimitMiddleware
from app.config import Settings

logger = logging.getLogger(__name__)


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


async def configure_menu_button(bot: Bot, webapp_url: str) -> None:
    """Chat pastidagi "Menu" tugmasini WebApp'ga bog'laydi (initData bilan ochiladi)."""
    if not webapp_url:
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text=texts.MENU_BUTTON_TEXT, web_app=WebAppInfo(url=webapp_url))
        )
    except TelegramAPIError as exc:
        logger.warning("Menu tugmasini sozlab bo'lmadi: %s", exc)
