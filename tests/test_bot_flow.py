"""Bot handlerlari ulanishini tekshirish: soxta Telegram sessiyasi orqali haqiqiy update'lar."""
from datetime import datetime

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, EditMessageText, SendMessage, TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from app.bot.callbacks import MODE_ADD, NavCb
from app.bot.setup import build_dispatcher
from app.config import Settings
from tests.conftest import FakeAI

_CHAT = Chat(id=500, type="private")


class RecordingSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.requests: list[TelegramMethod] = []

    async def make_request(self, bot, method, timeout=None):
        self.requests.append(method)
        if isinstance(method, (SendMessage, EditMessageText)):
            return Message(message_id=len(self.requests), date=datetime.now(), chat=_CHAT, text=method.text)
        return True

    async def stream_content(self, *args, **kwargs):
        yield b""

    async def close(self):
        return None


def _setup(admin="777"):
    settings = Settings(bot_token="42:TEST", admin_telegram_ids=admin, webapp_url="https://example.org")
    session = RecordingSession()
    bot = Bot(token="42:TEST", session=session)
    return bot, build_dispatcher(settings, FakeAI()), session


def _user(uid):
    return User(id=uid, is_bot=False, first_name="Ali")


def _text_update(uid, text, update_id=1):
    msg = Message(message_id=update_id, date=datetime.now(), chat=_CHAT, from_user=_user(uid), text=text)
    return Update(update_id=update_id, message=msg)


def _callback_update(uid, data, update_id=10):
    msg = Message(message_id=99, date=datetime.now(), chat=_CHAT, from_user=_user(uid), text="x")
    call = CallbackQuery(id="c1", from_user=_user(uid), chat_instance="ci", message=msg, data=data)
    return Update(update_id=update_id, callback_query=call)


def _texts(session):
    return [r.text for r in session.requests if isinstance(r, (SendMessage, EditMessageText))]


async def test_start_and_search_not_found(db):
    bot, dp, session = _setup()
    await dp.feed_update(bot, _text_update(100, "/start"))
    await dp.feed_update(bot, _text_update(100, "Yo'q kitob nomi", update_id=2))
    texts = _texts(session)
    assert "Books Road" in texts[0]
    assert "topilmadi" in texts[1]


async def test_short_query_handled_by_error_router(db):
    bot, dp, session = _setup()
    await dp.feed_update(bot, _text_update(100, "a"))
    assert "qisqa" in _texts(session)[0]


async def test_customer_cannot_open_add_flow(db):
    bot, dp, session = _setup()
    data = NavCb(mode=MODE_ADD, step="sec").pack()
    await dp.feed_update(bot, _callback_update(100, data))
    alerts = [r for r in session.requests if isinstance(r, AnswerCallbackQuery)]
    assert alerts and "xodim" in alerts[0].text


async def test_owner_navigates_to_photo_request(db):
    bot, dp, session = _setup(admin="777")
    await dp.feed_update(bot, _text_update(777, "➕ Javonga qo'shish"))
    assert "Bo'limni tanlang" in _texts(session)[-1]
    await dp.feed_update(bot, _callback_update(777, NavCb(mode=MODE_ADD, step="pick", section_id=1,
                                                           shelf_id=3, level=5).pack()))
    assert "A3 javon (old tomon) → 5-qator" in _texts(session)[-1]


async def test_webapp_button_sends_inline_web_app(db):
    """Reply-tugmada initData kelmaydi, shuning uchun bot inline web_app tugma yuboradi."""
    bot, dp, session = _setup()
    await dp.feed_update(bot, _text_update(100, "🗺 Do'kon xaritasi"))
    sent = [r for r in session.requests if isinstance(r, SendMessage)][-1]
    button = sent.reply_markup.inline_keyboard[0][0]
    assert button.web_app.url == "https://example.org"
