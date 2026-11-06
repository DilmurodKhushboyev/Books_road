"""Javon rasmidan narsalarni tanib olish -> tasdiqlash -> bazaga yozish.

Bosqichlar alohida tranzaksiyalarda: AI kutilayotganda baza ulanishi band qilinmaydi.
Bot ham, WebApp ham aynan shu funksiyalarni chaqiradi.
"""
import asyncio
import base64
import logging
from datetime import datetime, timedelta, timezone

from app.ai.base import AIProvider, DetectedItem
from app.constants import (
    AI_LOW_CONFIDENCE, BATCH_CANCELLED, BATCH_CONFIRMED, BATCH_PENDING, BATCH_TTL_HOURS,
)
from app.db.models import RecognitionBatch
from app.db.session import session_scope
from app.repositories import batch_repo, item_repo, layout_repo
from app.services import image_utils
from app.services.access_service import UserContext, require_editor
from app.services.batch_edits import BatchEdit, apply_edits, batch_view
from app.services.catalog_service import CatalogError, ItemInput, place_item, upsert_item

logger = logging.getLogger(__name__)


class RecognitionError(ValueError):
    """Partiya bilan ishlashda biznes-xato (kod: shelf_not_found, bad_level, ...)."""


def _process_image(photo: bytes) -> tuple[object, bytes]:
    image = image_utils.load_image(photo)
    return image, image_utils.prepare_for_ai(image)


def _enrich(image, detected: list[DetectedItem]) -> list[dict]:
    """Har bir narsa uchun kesilgan kichik rasm va dominant ranglar (vizual xotira)."""
    items = []
    for item in detected:
        crop = image_utils.crop_box(image, item.box)
        items.append({
            "title": item.title, "author": item.author, "kind": item.kind,
            "colors": item.colors, "shape": item.shape,
            "visual_description": item.visual_description,
            "quantity": item.quantity, "confidence": round(item.confidence, 2),
            "color_hex": image_utils.dominant_colors(crop),
            "thumb_b64": base64.b64encode(image_utils.make_thumbnail(crop)).decode(),
            "include": item.confidence >= AI_LOW_CONFIDENCE,
        })
    return items


async def _validate_target(ctx: UserContext, shelf_id: int, level: int) -> None:
    async with session_scope() as session:
        shelf = await layout_repo.get_shelf(session, ctx.store_id, shelf_id)
        if shelf is None:
            raise RecognitionError("shelf_not_found")
        if not 1 <= level <= shelf.levels_count:
            raise RecognitionError("bad_level")


async def recognize_shelf_photo(
    ai: AIProvider, ctx: UserContext, shelf_id: int, level: int, photo: bytes
) -> dict:
    require_editor(ctx)
    await _validate_target(ctx, shelf_id, level)
    image, ai_bytes = await asyncio.to_thread(_process_image, photo)
    detected = await ai.detect_items(ai_bytes)
    items = await asyncio.to_thread(_enrich, image, detected)
    avg = sum(i["confidence"] for i in items) / len(items) if items else 0.0
    async with session_scope() as session:
        batch = await batch_repo.create_batch(session, RecognitionBatch(
            store_id=ctx.store_id, user_id=ctx.user_id, shelf_id=shelf_id, level=level,
            status=BATCH_PENDING, items=items, avg_confidence=round(avg, 2),
        ))
        logger.info("batch=%s user=%s shelf=%s level=%s items=%s avg=%.2f",
                    batch.id, ctx.user_id, shelf_id, level, len(items), avg)
        return batch_view(batch)


def _is_expired(batch: RecognitionBatch) -> bool:
    created = batch.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - created > timedelta(hours=BATCH_TTL_HOURS)


async def _load_pending(session, ctx: UserContext, batch_id: int) -> RecognitionBatch:
    batch = await batch_repo.get_user_batch(session, batch_id, ctx.user_id)
    if batch is None:
        raise RecognitionError("batch_not_found")
    if batch.status != BATCH_PENDING:
        raise RecognitionError("batch_closed")
    if _is_expired(batch):
        raise RecognitionError("batch_expired")
    return batch


async def get_batch(ctx: UserContext, batch_id: int) -> dict:
    async with session_scope() as session:
        batch = await batch_repo.get_user_batch(session, batch_id, ctx.user_id)
        if batch is None:
            raise RecognitionError("batch_not_found")
        return batch_view(batch)


async def edit_batch(ctx: UserContext, batch_id: int, edits: list[BatchEdit]) -> dict:
    require_editor(ctx)
    async with session_scope() as session:
        batch = await _load_pending(session, ctx, batch_id)
        batch.items = apply_edits(batch.items, edits)
        return batch_view(batch)


async def confirm_batch(ctx: UserContext, batch_id: int, edits: list[BatchEdit] | None = None) -> dict:
    """Tasdiqlash idempotent: ikki marta bosilsa ikkinchisi 'batch_closed' oladi."""
    require_editor(ctx)
    async with session_scope() as session:
        batch = await _load_pending(session, ctx, batch_id)
        items = apply_edits(batch.items, edits or [])
        if not await batch_repo.claim_batch(session, batch.id, BATCH_CONFIRMED):
            raise RecognitionError("batch_closed")
        quantities: dict[int, int] = {}
        saved = 0
        for raw in items:
            if not raw.get("include"):
                continue
            data = ItemInput(**{k: raw[k] for k in ItemInput.__dataclass_fields__ if k in raw})
            try:
                item = await upsert_item(session, ctx.store_id, ctx.user_id, data)
            except CatalogError:
                logger.warning("batch=%s: bo'sh nomli element o'tkazib yuborildi", batch.id)
                continue
            # Bir rasmda bir xil narsa ikki joyda bo'lsa — sonlari qo'shiladi
            quantities[item.id] = quantities.get(item.id, 0) + data.cleaned().quantity
            if raw.get("thumb_b64"):
                await item_repo.add_image(session, item.id, base64.b64decode(raw["thumb_b64"]), "shelf_photo")
            saved += 1
        for item_id, quantity in quantities.items():
            await place_item(session, item_id, batch.shelf_id, batch.level, quantity, ctx.user_id)
        batch.items = [{**i, "thumb_b64": ""} for i in items]   # bazani yengillatamiz
        logger.info("batch=%s confirmed user=%s saved=%s", batch.id, ctx.user_id, saved)
        return {"batch_id": batch.id, "saved": saved, "skipped": len(items) - saved}


async def cancel_batch(ctx: UserContext, batch_id: int) -> None:
    async with session_scope() as session:
        await _load_pending(session, ctx, batch_id)
        if not await batch_repo.claim_batch(session, batch_id, BATCH_CANCELLED):
            raise RecognitionError("batch_closed")
