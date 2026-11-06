"""Kirish nuqtasi: baza -> do'kon andozasi -> AI -> bot (polling/webhook) + WebApp API."""
import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import uvicorn
from fastapi import FastAPI

from app.ai.factory import build_ai_provider
from app.api.app import create_app
from app.bot.setup import build_bot, build_dispatcher
from app.bot.webhook import WEBHOOK_PATH, build_webhook_router
from app.config import Settings, get_settings
from app.db.session import dispose_engine, init_engine, session_scope
from app.logging_setup import setup_logging
from app.services.layout_service import ensure_default_store

logger = logging.getLogger("app.main")


def build_application(settings: Settings) -> FastAPI:
    init_engine(settings.database_url)
    ai = build_ai_provider(settings)
    bot = build_bot(settings) if settings.bot_token else None
    dp = build_dispatcher(settings, ai) if bot else None
    routers = [build_webhook_router(bot, dp, settings.webhook_secret)] if bot and settings.use_webhook else []

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with session_scope() as session:
            await ensure_default_store(session)
        polling_task = None
        if bot and settings.use_webhook:
            await bot.set_webhook(f"{settings.public_url}{WEBHOOK_PATH}", secret_token=settings.webhook_secret,
                                  drop_pending_updates=False)
            logger.info("Bot webhook rejimida ishga tushdi")
        elif bot:
            await bot.delete_webhook(drop_pending_updates=False)
            polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
            logger.info("Bot polling rejimida ishga tushdi")
        else:
            logger.warning("BOT_TOKEN berilmagan — faqat WebApp API ishlaydi")
        try:
            yield
        finally:
            if polling_task:
                with suppress(Exception):
                    await dp.stop_polling()
                polling_task.cancel()
                with suppress(asyncio.CancelledError):
                    await polling_task
            if bot:
                await bot.session.close()
            if hasattr(ai, "close"):
                await ai.close()
            await dispose_engine()

    return create_app(settings, ai, lifespan=lifespan, extra_routers=routers)


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    app = build_application(settings)
    uvicorn.run(app, host="0.0.0.0", port=settings.port, log_level=settings.log_level.lower(),
                proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
