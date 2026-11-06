"""Katalog: mahsulotni saqlash (takrorlanmasdan), joylashtirish va qoldiqni boshqarish."""
import logging
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    DEFAULT_KIND, KIND_LABELS, MAX_AUTHOR_LEN, MAX_DESCRIPTION_LEN, MAX_QUANTITY, MAX_TITLE_LEN,
    STATUS_IN_STOCK, STATUS_OUT,
)
from app.db.models import Item, Placement
from app.repositories import item_repo
from app.services.access_service import UserContext, require_editor
from app.services.text_normalize import clean_user_text, normalize_text

logger = logging.getLogger(__name__)

STOCK_ACTIONS = ("inc", "dec", "out", "in")


class CatalogError(ValueError):
    """Katalog amali bajarilmadi (topilmadi / noto'g'ri qiymat)."""


@dataclass
class ItemInput:
    title: str
    author: str = ""
    kind: str = DEFAULT_KIND
    colors: list[str] = field(default_factory=list)
    color_hex: list[str] = field(default_factory=list)
    shape: str = ""
    visual_description: str = ""
    quantity: int = 1

    def cleaned(self) -> "ItemInput":
        title = clean_user_text(self.title, MAX_TITLE_LEN)
        if not normalize_text(title):
            raise CatalogError("empty_title")
        return ItemInput(
            title=title,
            author=clean_user_text(self.author, MAX_AUTHOR_LEN),
            kind=self.kind if self.kind in KIND_LABELS else DEFAULT_KIND,
            colors=[clean_user_text(c, 40) for c in self.colors[:5] if c],
            color_hex=[c for c in self.color_hex[:5] if isinstance(c, str) and len(c) == 7],
            shape=clean_user_text(self.shape, 64),
            visual_description=clean_user_text(self.visual_description, MAX_DESCRIPTION_LEN),
            quantity=max(1, min(MAX_QUANTITY, int(self.quantity or 1))),
        )


async def upsert_item(session: AsyncSession, store_id: int, user_id: int, data: ItemInput) -> Item:
    """Bir xil nom+muallif bo'lsa mavjudini qaytaradi (dublikat yaratilmaydi)."""
    data = data.cleaned()
    title_norm, author_norm = normalize_text(data.title), normalize_text(data.author)
    item = await item_repo.find_item(session, store_id, title_norm, author_norm)
    if item is None:
        item = Item(
            store_id=store_id, kind=data.kind, title=data.title, author=data.author,
            title_norm=title_norm, author_norm=author_norm,
            search_norm=f"{title_norm} {author_norm}".strip(), created_by=user_id,
        )
        item = await item_repo.add_item(session, item)
    # Vizual xotirani to'ldiramiz (bo'sh bo'lsa) — keyingi rasm qidiruvlari uchun
    item.colors = item.colors or data.colors
    item.color_hex = item.color_hex or data.color_hex
    item.shape = item.shape or data.shape
    item.visual_description = item.visual_description or data.visual_description
    if item.kind == DEFAULT_KIND and data.kind != DEFAULT_KIND:
        item.kind = data.kind
    return item


async def place_item(
    session: AsyncSession, item_id: int, shelf_id: int, level: int, quantity: int, user_id: int
) -> Placement:
    """Joylashuvni yaratadi yoki yangilaydi (qayta skanerlash = joriy son)."""
    quantity = max(1, min(MAX_QUANTITY, quantity))
    placement = await item_repo.find_placement(session, item_id, shelf_id, level)
    if placement is None:
        return await item_repo.add_placement(session, Placement(
            item_id=item_id, shelf_id=shelf_id, level=level, quantity=quantity,
            status=STATUS_IN_STOCK, updated_by=user_id,
        ))
    placement.quantity = quantity
    placement.status = STATUS_IN_STOCK
    placement.updated_by = user_id
    return placement


def apply_stock_action(placement: Placement, action: str) -> None:
    if action not in STOCK_ACTIONS:
        raise CatalogError("bad_action")
    if action == "inc":
        placement.quantity = min(MAX_QUANTITY, placement.quantity + 1)
        placement.status = STATUS_IN_STOCK
    elif action == "dec":
        placement.quantity = max(0, placement.quantity - 1)
        placement.status = STATUS_IN_STOCK if placement.quantity > 0 else STATUS_OUT
    elif action == "out":
        placement.quantity = 0
        placement.status = STATUS_OUT
    else:
        placement.quantity = max(1, placement.quantity)
        placement.status = STATUS_IN_STOCK


async def change_stock(
    session: AsyncSession, ctx: UserContext, placement_id: int, action: str
) -> Placement:
    require_editor(ctx)
    placement = await item_repo.get_placement(session, ctx.store_id, placement_id)
    if placement is None:
        raise CatalogError("not_found")
    apply_stock_action(placement, action)
    placement.updated_by = ctx.user_id
    await session.flush()
    logger.info("stock user=%s placement=%s action=%s qty=%s", ctx.user_id, placement_id, action, placement.quantity)
    return placement
