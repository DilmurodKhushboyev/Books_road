"""Javon rasmini yuklash -> AI natijasini ko'rib chiqish -> tasdiqlash (faqat xodimlar)."""
import re
from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.ai.base import AIProvider
from app.bot import formatters, keyboards, texts
from app.bot.callbacks import MODE_ADD, BatchCb
from app.bot.photo_io import PHOTO_FILTER, download_photo
from app.bot.states import AddFlow
from app.constants import LEVEL_NUMBERING_HINT
from app.services import recognition_service
from app.services.access_service import UserContext, require_editor
from app.services.batch_edits import BatchEdit
from app.services.rate_limit import ai_limiter
from app.texts import error_text

_EDIT_RE = re.compile(r"^\s*(\d{1,3})\s*[:.)\-]\s*(.+)$", re.DOTALL)
_DEFAULT_LEVELS = 8


async def on_shelf_photo(message: Message, bot: Bot, state: FSMContext, ctx: UserContext, ai: AIProvider) -> None:
    require_editor(ctx)
    if not ai_limiter.allow(ctx.telegram_id):
        await message.answer(error_text("rate_limited"))
        return
    data = await state.get_data()
    photo = await download_photo(bot, message)
    progress = await message.answer(texts.ANALYZING)
    try:
        batch = await recognition_service.recognize_shelf_photo(ai, ctx, data["shelf_id"], data["level"], photo)
    finally:
        await progress.delete()
    if not batch["items"]:
        await state.set_state(AddFlow.waiting_photo)
        await message.answer(texts.NOTHING_DETECTED)
        return
    await state.set_state(AddFlow.reviewing)
    await state.update_data(batch_id=batch["batch_id"])
    await message.answer(formatters.batch_review(batch, data["location"]), reply_markup=keyboards.batch_review(batch))


async def on_edit_text(message: Message, state: FSMContext, ctx: UserContext) -> None:
    """'3: Nom | Muallif' — AI xato o'qigan nomni tuzatish."""
    match = _EDIT_RE.match(message.text)
    title, _, author = match.group(2).partition("|")
    edit = BatchEdit(index=int(match.group(1)) - 1, title=title.strip(), include=True,
                     author=author.strip() if author else None)
    data = await state.get_data()
    batch = await recognition_service.edit_batch(ctx, data["batch_id"], [edit])
    await message.answer(texts.EDIT_DONE.format(index=match.group(1)))
    await message.answer(formatters.batch_review(batch, data["location"]), reply_markup=keyboards.batch_review(batch))


async def on_toggle(call: CallbackQuery, callback_data: BatchCb, state: FSMContext, ctx: UserContext) -> None:
    current = await recognition_service.get_batch(ctx, callback_data.batch_id)
    items = current["items"]
    if not 0 <= callback_data.index < len(items):
        await call.answer()
        return
    edit = BatchEdit(index=callback_data.index, include=not items[callback_data.index]["include"])
    batch = await recognition_service.edit_batch(ctx, callback_data.batch_id, [edit])
    location = (await state.get_data()).get("location", "")
    await call.message.edit_text(formatters.batch_review(batch, location), reply_markup=keyboards.batch_review(batch))
    await call.answer()


async def on_confirm(call: CallbackQuery, callback_data: BatchCb, state: FSMContext, ctx: UserContext) -> None:
    data = await state.get_data()
    result = await recognition_service.confirm_batch(ctx, callback_data.batch_id)
    await state.set_state(None)
    location = escape(data.get("location", ""))
    await call.message.edit_text(texts.CONFIRMED.format(saved=result["saved"], skipped=result["skipped"],
                                                        location=location))
    if data.get("section_id") and data.get("shelf_id"):
        # Shu javonning keyingi qatoriga tezda o'tish uchun
        await call.message.answer(
            texts.CHOOSE_LEVEL.format(shelf=escape(data.get("shelf_code", "")), hint=LEVEL_NUMBERING_HINT),
            reply_markup=keyboards.levels(MODE_ADD, data["section_id"], data["shelf_id"],
                                          data.get("levels_count", _DEFAULT_LEVELS)),
        )
    await call.answer(texts.STOCK_UPDATED)


async def on_cancel(call: CallbackQuery, callback_data: BatchCb, state: FSMContext, ctx: UserContext) -> None:
    await recognition_service.cancel_batch(ctx, callback_data.batch_id)
    await state.clear()
    await call.message.edit_text(texts.CANCELLED)
    await call.answer()


def build_router() -> Router:
    """Har chaqiruvda yangi router (bir nechta Dispatcher/test uchun xavfsiz)."""
    router = Router(name="add_items")
    router.message.register(on_shelf_photo, StateFilter(AddFlow.waiting_photo, AddFlow.reviewing), PHOTO_FILTER)
    router.message.register(on_edit_text, AddFlow.reviewing, F.text.regexp(_EDIT_RE))
    router.callback_query.register(on_toggle, BatchCb.filter(F.action == "t"))
    router.callback_query.register(on_confirm, BatchCb.filter(F.action == "ok"))
    router.callback_query.register(on_cancel, BatchCb.filter(F.action == "no"))
    return router
