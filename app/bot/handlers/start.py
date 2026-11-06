"""/start, /help, /myid, /add_staff va menyu tugmalari."""
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot import keyboards, texts
from app.config import Settings
from app.db.session import session_scope
from app.services.access_service import UserContext, grant_staff


async def cmd_start(message: Message, state: FSMContext, ctx: UserContext, settings: Settings) -> None:
    await state.clear()
    text = texts.WELCOME.format(name=escape(message.from_user.first_name or ""))
    if ctx.can_edit:
        text += texts.WELCOME_STAFF.format(add=texts.BTN_ADD)
    await message.answer(text, reply_markup=keyboards.main_menu(ctx.can_edit, settings.public_url))


async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP.format(add=texts.BTN_ADD))


async def cmd_myid(message: Message) -> None:
    await message.answer(texts.MY_ID.format(id=message.from_user.id))


async def cmd_add_staff(message: Message, command: CommandObject, ctx: UserContext) -> None:
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer(texts.ADD_STAFF_USAGE)
        return
    async with session_scope() as session:
        found = await grant_staff(session, ctx, int(arg))
    await message.answer(texts.STAFF_ADDED if found else texts.STAFF_NOT_FOUND)


async def btn_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.ASK_QUERY)


async def btn_webapp(message: Message, settings: Settings) -> None:
    """WebApp'ni inline tugma bilan ochamiz (reply-tugmada initData kelmaydi)."""
    if not settings.public_url:
        await message.answer(texts.WEBAPP_NOT_CONFIGURED)
        return
    await message.answer(texts.OPEN_WEBAPP, reply_markup=keyboards.webapp_inline(settings.public_url))


def build_router() -> Router:
    """Har chaqiruvda yangi router (bir nechta Dispatcher/test uchun xavfsiz)."""
    router = Router(name="start")
    router.message.register(cmd_start, CommandStart())
    router.message.register(cmd_help, Command("help"))
    router.message.register(cmd_myid, Command("myid"))
    router.message.register(cmd_add_staff, Command("add_staff"))
    router.message.register(btn_search, F.text == texts.BTN_SEARCH)
    router.message.register(btn_webapp, F.text == texts.BTN_WEBAPP)
    return router
