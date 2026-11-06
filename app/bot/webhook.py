"""Webhook rejimi: Telegram update'larini FastAPI orqali qabul qilish."""
import hmac
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Header, Request, Response

logger = logging.getLogger(__name__)
WEBHOOK_PATH = "/telegram/webhook"


def build_webhook_router(bot: Bot, dp: Dispatcher, secret: str) -> APIRouter:
    router = APIRouter()

    @router.post(WEBHOOK_PATH, include_in_schema=False)
    async def telegram_webhook(
        request: Request, x_telegram_bot_api_secret_token: str = Header(default="")
    ) -> Response:
        if not hmac.compare_digest(x_telegram_bot_api_secret_token, secret):
            return Response(status_code=403)
        try:
            update = Update.model_validate(await request.json(), context={"bot": bot})
        except ValueError:
            logger.warning("Webhook: noto'g'ri update")
            return Response(status_code=400)
        await dp.feed_update(bot, update)
        return Response(status_code=200)

    return router
