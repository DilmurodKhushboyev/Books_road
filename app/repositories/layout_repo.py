"""Do'kon, bo'lim va javonlar bo'yicha baza so'rovlari."""
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import STATUS_IN_STOCK
from app.db.models import Placement, Section, Shelf, Store


async def get_store_by_slug(session: AsyncSession, slug: str) -> Store | None:
    result = await session.execute(select(Store).where(Store.slug == slug))
    return result.scalar_one_or_none()


async def create_store(session: AsyncSession, slug: str, name: str) -> Store:
    store = Store(slug=slug, name=name)
    session.add(store)
    await session.flush()
    return store


async def count_sections(session: AsyncSession, store_id: int) -> int:
    result = await session.execute(
        select(func.count(Section.id)).where(Section.store_id == store_id)
    )
    return int(result.scalar_one())


async def list_sections(session: AsyncSession, store_id: int) -> list[Section]:
    result = await session.execute(
        select(Section).where(Section.store_id == store_id).order_by(Section.position)
    )
    return list(result.scalars().unique().all())


async def get_section(session: AsyncSession, store_id: int, section_id: int) -> Section | None:
    result = await session.execute(
        select(Section).where(Section.id == section_id, Section.store_id == store_id)
    )
    return result.scalar_one_or_none()


async def get_shelf(session: AsyncSession, store_id: int, shelf_id: int) -> Shelf | None:
    """Javonni faqat shu do'konga tegishli bo'lsa qaytaradi (begona ID himoyasi)."""
    result = await session.execute(
        select(Shelf).join(Section).where(Shelf.id == shelf_id, Section.store_id == store_id)
    )
    return result.scalar_one_or_none()


async def shelf_stock_counts(session: AsyncSession, store_id: int) -> dict[int, tuple[int, int]]:
    """{shelf_id: (bor_soni, jami_soni)} — bitta GROUP BY so'rovi bilan."""
    in_stock = func.sum(case((Placement.status == STATUS_IN_STOCK, 1), else_=0))
    result = await session.execute(
        select(Placement.shelf_id, in_stock, func.count(Placement.id))
        .join(Shelf, Shelf.id == Placement.shelf_id)
        .join(Section, Section.id == Shelf.section_id)
        .where(Section.store_id == store_id)
        .group_by(Placement.shelf_id)
    )
    return {row[0]: (int(row[1] or 0), int(row[2])) for row in result.all()}
