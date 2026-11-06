"""Nom bo'yicha qidiruv (oddiy matn) va qoldiqni o'zgartirish tugmalari."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot import formatters, keyboards, texts
from app.bot.callbacks import StockCb
from app.db.session import session_scope
from app.services import catalog_service, search_service
from app.services.access_service import UserContext


async def on_text_search(message: Message, ctx: UserContext) -> None:
    query = message.text.strip()
    async with session_scope() as session:
        views = await search_service.search_items(session, ctx.store_id, query)
    markup = keyboards.stock_controls(views) if ctx.can_edit else None
    await message.answer(formatters.search_results(query, views), reply_markup=markup)


async def on_stock(call: CallbackQuery, callback_data: StockCb, ctx: UserContext) -> None:
    async with session_scope() as session:
        placement = await catalog_service.change_stock(
            session, ctx, callback_data.placement_id, callback_data.action
        )
        quantity = placement.quantity
    status = texts.IN_STOCK.format(qty=quantity) if quantity > 0 else texts.OUT_OF_STOCK
    await call.answer(f"{texts.STOCK_UPDATED}\n{status}", show_alert=True)


async def on_unsupported(message: Message) -> None:
    """Noma'lum buyruq, stiker, ovoz va h.k. — qisqa yo'l-yo'riq."""
    await message.answer(texts.HELP.format(add=texts.BTN_ADD) if message.text else texts.ASK_QUERY)


def build_router() -> Router:
    """Har chaqiruvda yangi router (bir nechta Dispatcher/test uchun xavfsiz)."""
    router = Router(name="search")
    router.message.register(on_text_search, F.text & ~F.text.startswith("/"))
    router.callback_query.register(on_stock, StockCb.filter())
    router.message.register(on_unsupported)
    return router
