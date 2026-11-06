"""Rasm bo'yicha topish: foydalanuvchi narsa rasmini yuboradi -> joylashuvi."""
from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.ai.base import AIProvider
from app.bot import formatters, keyboards, texts
from app.bot.photo_io import PHOTO_FILTER, download_photo
from app.bot.states import FindFlow
from app.services import visual_match_service
from app.services.access_service import UserContext
from app.services.rate_limit import ai_limiter
from app.texts import error_text


async def btn_find_photo(message: Message, state: FSMContext) -> None:
    await state.set_state(FindFlow.waiting_photo)
    await message.answer(texts.ASK_FIND_PHOTO)


# Holatsiz yuborilgan rasm ham "rasm bilan topish" deb qabul qilinadi
async def on_find_photo(message: Message, bot: Bot, state: FSMContext, ctx: UserContext, ai: AIProvider) -> None:
    if not ai_limiter.allow(ctx.telegram_id):
        await message.answer(error_text("rate_limited"))
        return
    photo = await download_photo(bot, message)
    await state.clear()
    progress = await message.answer(texts.ANALYZING_FIND)
    try:
        result = await visual_match_service.find_by_photo(ai, ctx, photo)
    finally:
        await progress.delete()
    markup = keyboards.stock_controls(result["results"]) if ctx.can_edit else None
    await message.answer(formatters.photo_find_result(result), reply_markup=markup)


def build_router() -> Router:
    """Har chaqiruvda yangi router (bir nechta Dispatcher/test uchun xavfsiz)."""
    router = Router(name="find_photo")
    router.message.register(btn_find_photo, F.text == texts.BTN_FIND_PHOTO)
    router.message.register(on_find_photo, StateFilter(None, FindFlow.waiting_photo), PHOTO_FILTER)
    return router
