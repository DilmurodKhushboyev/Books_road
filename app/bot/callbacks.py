"""Inline tugmalar ma'lumotlari (Telegram cheklovi: 64 bayt)."""
from aiogram.filters.callback_data import CallbackData

MODE_BROWSE = "b"
MODE_ADD = "a"


class NavCb(CallbackData, prefix="nav"):
    mode: str                 # b — ko'rish, a — qo'shish
    step: str                 # sec | shelf | lvl | pick
    section_id: int = 0
    shelf_id: int = 0
    level: int = 0


class BatchCb(CallbackData, prefix="bt"):
    action: str               # t (toggle) | ok | no
    batch_id: int
    index: int = -1


class StockCb(CallbackData, prefix="st"):
    action: str               # inc | dec | out | in
    placement_id: int
