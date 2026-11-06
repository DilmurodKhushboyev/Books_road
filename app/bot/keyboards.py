"""Klaviaturalar (reply va inline)."""
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import texts
from app.bot.callbacks import BatchCb, NavCb, StockCb

_SHELF_ROW = 5
_TOGGLE_ROW = 6
_LEVEL_ROW = 4
_MAX_STOCK_BUTTON_ROWS = 5


def main_menu(can_edit: bool, webapp_url: str) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=texts.BTN_SEARCH), KeyboardButton(text=texts.BTN_FIND_PHOTO)],
            [KeyboardButton(text=texts.BTN_BROWSE)]]
    if can_edit:
        rows[1].append(KeyboardButton(text=texts.BTN_ADD))
    if webapp_url:
        rows.append([KeyboardButton(text=texts.BTN_WEBAPP, web_app=WebAppInfo(url=webapp_url))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def sections(mode: str, sections_view: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for section in sections_view:
        builder.button(text=section["name"],
                       callback_data=NavCb(mode=mode, step="shelf", section_id=section["id"]))
    builder.adjust(1)
    return builder.as_markup()


def shelves(mode: str, section: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for shelf in section["shelves"]:
        arrow = "⬆️" if shelf["side"] == "front" else "⬇️"
        builder.button(text=f"{arrow}{shelf['code']} ({shelf['in_stock']})",
                       callback_data=NavCb(mode=mode, step="lvl", section_id=section["id"],
                                           shelf_id=shelf["id"]))
    builder.adjust(_SHELF_ROW)
    builder.row(InlineKeyboardButton(
        text="⬅️ Bo'limlar", callback_data=NavCb(mode=mode, step="sec").pack()))
    return builder.as_markup()


def levels(mode: str, section_id: int, shelf_id: int, levels_count: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for level in range(1, levels_count + 1):
        builder.button(text=f"{level}-qator",
                       callback_data=NavCb(mode=mode, step="pick", section_id=section_id,
                                           shelf_id=shelf_id, level=level))
    builder.adjust(_LEVEL_ROW)
    builder.row(InlineKeyboardButton(
        text="⬅️ Javonlar", callback_data=NavCb(mode=mode, step="shelf", section_id=section_id).pack()))
    return builder.as_markup()


def batch_review(batch: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in batch["items"]:
        mark = "✅" if item["include"] else "▫️"
        builder.button(text=f"{mark}{item['index'] + 1}",
                       callback_data=BatchCb(action="t", batch_id=batch["batch_id"], index=item["index"]))
    builder.adjust(_TOGGLE_ROW)
    count = sum(1 for item in batch["items"] if item["include"])
    builder.row(
        InlineKeyboardButton(text=f"💾 Tasdiqlash ({count})",
                             callback_data=BatchCb(action="ok", batch_id=batch["batch_id"]).pack()),
        InlineKeyboardButton(text="❌ Bekor",
                             callback_data=BatchCb(action="no", batch_id=batch["batch_id"]).pack()),
    )
    return builder.as_markup()


def stock_controls(views: list[dict]) -> InlineKeyboardMarkup | None:
    """Xodim uchun: har joylashuvga ➖ / ➕ / ❌ tugmalari (birinchi bir nechtasi)."""
    rows: list[list[InlineKeyboardButton]] = []
    for number, view in enumerate(views, start=1):
        for place in view["placements"]:
            if len(rows) >= _MAX_STOCK_BUTTON_ROWS:
                break
            pid = place["placement_id"]
            label = f"{number}. {place['shelf_code']}/{place['level']}"
            rows.append([
                InlineKeyboardButton(text=f"➖ {label}", callback_data=StockCb(action="dec", placement_id=pid).pack()),
                InlineKeyboardButton(text="➕", callback_data=StockCb(action="inc", placement_id=pid).pack()),
                InlineKeyboardButton(text="❌ Qolmadi", callback_data=StockCb(action="out", placement_id=pid).pack()),
            ])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
