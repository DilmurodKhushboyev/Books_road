"""FSM holatlari (faqat ID lar saqlanadi; ma'lumotning o'zi bazada)."""
from aiogram.fsm.state import State, StatesGroup


class AddFlow(StatesGroup):
    waiting_photo = State()       # data: shelf_id, level, location
    reviewing = State()           # data: batch_id, location


class FindFlow(StatesGroup):
    waiting_photo = State()
