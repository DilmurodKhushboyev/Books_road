"""Bo'lim -> javon -> qator navigatsiyasi (ko'rish va qo'shish rejimlari uchun umumiy)."""
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot import formatters, keyboards, texts
from app.bot.callbacks import MODE_ADD, MODE_BROWSE, NavCb
from app.bot.states import AddFlow
from app.constants import LEVEL_NUMBERING_HINT
from app.db.session import session_scope
from app.services import layout_service, shelf_service
from app.services.access_service import UserContext, require_editor


async def _layout(ctx: UserContext) -> list[dict]:
    async with session_scope() as session:
        return await layout_service.layout_view(session, ctx.store_id)


def _find(items: list[dict], item_id: int) -> dict | None:
    return next((item for item in items if item["id"] == item_id), None)


async def btn_browse(message: Message, state: FSMContext, ctx: UserContext) -> None:
    await state.clear()
    await message.answer(texts.CHOOSE_SECTION, reply_markup=keyboards.sections(MODE_BROWSE, await _layout(ctx)))


async def btn_add(message: Message, state: FSMContext, ctx: UserContext) -> None:
    require_editor(ctx)
    await state.clear()
    await message.answer(texts.CHOOSE_SECTION, reply_markup=keyboards.sections(MODE_ADD, await _layout(ctx)))


async def on_nav(call: CallbackQuery, callback_data: NavCb, state: FSMContext, ctx: UserContext) -> None:
    if callback_data.mode == MODE_ADD:
        require_editor(ctx)
    layout = await _layout(ctx)
    section = _find(layout, callback_data.section_id)
    if callback_data.step == "sec" or section is None:
        await call.message.edit_text(texts.CHOOSE_SECTION,
                                     reply_markup=keyboards.sections(callback_data.mode, layout))
    elif callback_data.step == "shelf":
        await call.message.edit_text(texts.CHOOSE_SHELF.format(section=escape(section["name"])),
                                     reply_markup=keyboards.shelves(callback_data.mode, section))
    else:
        shelf = _find(section["shelves"], callback_data.shelf_id)
        if shelf is None:
            await call.answer(texts.CHOOSE_SECTION, show_alert=True)
            return
        if callback_data.step == "lvl":
            await call.message.edit_text(
                texts.CHOOSE_LEVEL.format(shelf=escape(shelf["code"]), hint=LEVEL_NUMBERING_HINT),
                reply_markup=keyboards.levels(callback_data.mode, section["id"], shelf["id"], shelf["levels_count"]),
            )
        elif callback_data.mode == MODE_BROWSE:
            await _show_level(call, ctx, section["id"], shelf, callback_data.level)
        else:
            await _ask_shelf_photo(call, state, section, shelf, callback_data.level)
    await call.answer()


async def _show_level(call: CallbackQuery, ctx: UserContext, section_id: int, shelf: dict, level: int) -> None:
    async with session_scope() as session:
        contents = await shelf_service.shelf_contents(session, ctx.store_id, shelf["id"], level)
    await call.message.edit_text(
        formatters.shelf_level(contents),
        reply_markup=keyboards.levels(MODE_BROWSE, section_id, shelf["id"], shelf["levels_count"]),
    )


async def _ask_shelf_photo(call: CallbackQuery, state: FSMContext, section: dict, shelf: dict, level: int) -> None:
    if not 1 <= level <= shelf["levels_count"]:
        await call.answer(texts.CHOOSE_SECTION, show_alert=True)
        return
    location = layout_service.location_text(section["code"], shelf["code"], shelf["side"], level)
    await state.set_state(AddFlow.waiting_photo)
    await state.update_data(shelf_id=shelf["id"], shelf_code=shelf["code"], section_id=section["id"],
                            levels_count=shelf["levels_count"], level=level, location=location)
    await call.message.edit_text(texts.SEND_SHELF_PHOTO.format(location=escape(location)))


def build_router() -> Router:
    """Har chaqiruvda yangi router (bir nechta Dispatcher/test uchun xavfsiz)."""
    router = Router(name="browse")
    router.message.register(btn_browse, F.text == texts.BTN_BROWSE)
    router.message.register(btn_add, F.text == texts.BTN_ADD)
    router.callback_query.register(on_nav, NavCb.filter())
    return router
