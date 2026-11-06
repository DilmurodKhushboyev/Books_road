"""Global xato handler: domen xatolari -> tushunarli xabar; kutilmagan -> log + umumiy xabar."""
import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ErrorEvent

from app.ai.base import AIError, AIUnavailable
from app.services.access_service import AccessDenied
from app.services.catalog_service import CatalogError
from app.services.image_utils import InvalidImage
from app.services.recognition_service import RecognitionError
from app.services.search_service import InvalidQuery
from app.services.shelf_service import ShelfNotFound
from app.texts import error_text

logger = logging.getLogger(__name__)


def error_code(exc: Exception) -> str:
    if isinstance(exc, AccessDenied):
        return "forbidden"
    if isinstance(exc, AIUnavailable):
        return "ai_unavailable"
    if isinstance(exc, AIError):
        return "ai_error"
    if isinstance(exc, InvalidImage):
        return "invalid_image"
    if isinstance(exc, ShelfNotFound):
        return "shelf_not_found"
    if isinstance(exc, (InvalidQuery, RecognitionError, CatalogError)):
        return str(exc)
    return "internal"


async def on_error(event: ErrorEvent) -> bool:
    exc = event.exception
    code = error_code(exc)
    if isinstance(exc, TelegramBadRequest) and "message is not modified" in str(exc):
        return True
    if code == "internal":
        logger.exception("Bot xatosi (update=%s)", event.update.update_id, exc_info=exc)
    else:
        logger.info("Bot domen xatosi: %s (%s)", code, exc.__class__.__name__)
    text = error_text(code)
    try:
        if event.update.callback_query:
            await event.update.callback_query.answer(text, show_alert=True)
        elif event.update.message:
            await event.update.message.answer(text)
    except Exception:  # noqa: BLE001 — javob yuborib bo'lmasa ham log yoziladi
        logger.warning("Xato xabarini yuborib bo'lmadi (update=%s)", event.update.update_id)
    return True


def build_router() -> Router:
    """Har chaqiruvda yangi router (bir nechta Dispatcher/test uchun xavfsiz)."""
    router = Router(name="errors")
    router.errors.register(on_error)
    return router
