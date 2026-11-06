"""Mahsulot (Item), joylashuv (Placement) va rasm bo'yicha baza so'rovlari."""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item, ItemImage, Placement, Section, Shelf

# Qidiruv/ko'rsatish uchun kerakli ustunlar (SELECT * o'rniga)
_ITEM_LIST_COLUMNS = (
    Item.id, Item.kind, Item.title, Item.author, Item.search_norm,
    Item.colors, Item.color_hex, Item.shape, Item.visual_description,
)


async def find_item(
    session: AsyncSession, store_id: int, title_norm: str, author_norm: str
) -> Item | None:
    result = await session.execute(
        select(Item).where(
            Item.store_id == store_id,
            Item.title_norm == title_norm,
            Item.author_norm == author_norm,
        )
    )
    return result.scalars().first()


async def add_item(session: AsyncSession, item: Item) -> Item:
    session.add(item)
    await session.flush()
    return item


async def get_item(session: AsyncSession, store_id: int, item_id: int) -> Item | None:
    result = await session.execute(
        select(Item).where(Item.id == item_id, Item.store_id == store_id)
    )
    return result.scalar_one_or_none()


async def candidates_by_tokens(
    session: AsyncSession, store_id: int, tokens: list[str], limit: int
) -> list:
    """Har qanday token qatnashgan narsalar (Postgres'da pg_trgm indeks tezlashtiradi)."""
    if not tokens:
        return []
    conditions = [Item.search_norm.contains(token, autoescape=True) for token in tokens]
    result = await session.execute(
        select(*_ITEM_LIST_COLUMNS)
        .where(Item.store_id == store_id, or_(*conditions))
        .limit(limit)
    )
    return list(result.all())


async def candidates_by_kind(
    session: AsyncSession, store_id: int, kind: str | None, limit: int
) -> list:
    query = select(*_ITEM_LIST_COLUMNS).where(Item.store_id == store_id)
    if kind:
        query = query.where(Item.kind == kind)
    result = await session.execute(query.order_by(Item.updated_at.desc()).limit(limit))
    return list(result.all())


async def placements_for_items(session: AsyncSession, item_ids: list[int]) -> list:
    """Har bir joylashuv + javon + bo'lim ma'lumoti (bitta JOIN so'rovi)."""
    if not item_ids:
        return []
    result = await session.execute(
        select(
            Placement.id, Placement.item_id, Placement.level, Placement.quantity,
            Placement.status, Shelf.id.label("shelf_id"), Shelf.code.label("shelf_code"),
            Shelf.side, Section.code.label("section_code"), Section.name.label("section_name"),
        )
        .join(Shelf, Shelf.id == Placement.shelf_id)
        .join(Section, Section.id == Shelf.section_id)
        .where(Placement.item_id.in_(item_ids))
        .order_by(Section.position, Shelf.position, Placement.level)
    )
    return list(result.all())


async def items_on_shelf(session: AsyncSession, shelf_id: int, level: int | None = None) -> list:
    query = (
        select(
            Placement.id.label("placement_id"), Placement.level, Placement.quantity,
            Placement.status, Item.id.label("item_id"), Item.kind, Item.title, Item.author,
        )
        .join(Item, Item.id == Placement.item_id)
        .where(Placement.shelf_id == shelf_id)
    )
    if level is not None:
        query = query.where(Placement.level == level)
    result = await session.execute(query.order_by(Placement.level, Item.title))
    return list(result.all())


async def get_placement(session: AsyncSession, store_id: int, placement_id: int) -> Placement | None:
    result = await session.execute(
        select(Placement)
        .join(Item, Item.id == Placement.item_id)
        .where(Placement.id == placement_id, Item.store_id == store_id)
    )
    return result.scalar_one_or_none()


async def find_placement(
    session: AsyncSession, item_id: int, shelf_id: int, level: int
) -> Placement | None:
    result = await session.execute(
        select(Placement).where(
            Placement.item_id == item_id, Placement.shelf_id == shelf_id, Placement.level == level
        )
    )
    return result.scalar_one_or_none()


async def add_placement(session: AsyncSession, placement: Placement) -> Placement:
    session.add(placement)
    await session.flush()
    return placement


async def add_image(session: AsyncSession, item_id: int, thumbnail: bytes, source: str) -> None:
    session.add(ItemImage(item_id=item_id, thumbnail=thumbnail, source=source))
    await session.flush()


async def get_thumbnail(session: AsyncSession, store_id: int, item_id: int) -> bytes | None:
    result = await session.execute(
        select(ItemImage.thumbnail)
        .join(Item, Item.id == ItemImage.item_id)
        .where(ItemImage.item_id == item_id, Item.store_id == store_id)
        .order_by(ItemImage.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
