"""Telegram xabaridan rasmni xavfsiz yuklab olish."""
from aiogram import Bot, F
from aiogram.types import Message

from app.constants import MAX_PHOTO_BYTES
from app.services.image_utils import InvalidImage

# Siqilgan rasm yoki "fayl" sifatida yuborilgan rasm
PHOTO_FILTER = F.photo | (F.document & F.document.mime_type.startswith("image/"))


async def download_photo(bot: Bot, message: Message) -> bytes:
    media = message.photo[-1] if message.photo else message.document
    if media is None:
        raise InvalidImage("no_photo")
    if media.file_size and media.file_size > MAX_PHOTO_BYTES:
        raise InvalidImage("too_big")
    buffer = await bot.download(media)
    if buffer is None:
        raise InvalidImage("download_failed")
    data = buffer.read()
    if len(data) > MAX_PHOTO_BYTES:
        raise InvalidImage("too_big")
    return data
