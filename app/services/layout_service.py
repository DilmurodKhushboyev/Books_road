"""Do'kon andozasi: boshlang'ich yaratish (idempotent) va ko'rinish ma'lumotlari."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import DEFAULT_STORE_NAME, DEFAULT_STORE_SLUG
from app.db.models import Section, Shelf
from app.layout.default_layout import DEFAULT_LAYOUT, SIDE_LABELS, SectionSpec
from app.repositories import layout_repo

logger = logging.getLogger(__name__)


async def ensure_default_store(
    session: AsyncSession, layout: tuple[SectionSpec, ...] = DEFAULT_LAYOUT
) -> int:
    """Do'kon va javonlarni bir marta yaratadi; qayta chaqirilsa hech narsa o'zgarmaydi."""
    store = await layout_repo.get_store_by_slug(session, DEFAULT_STORE_SLUG)
    if store is None:
        store = await layout_repo.create_store(session, DEFAULT_STORE_SLUG, DEFAULT_STORE_NAME)
        logger.info("Do'kon yaratildi: id=%s", store.id)
    if await layout_repo.count_sections(session, store.id) > 0:
        return store.id
    for spec in layout:
        section = Section(store_id=store.id, code=spec.code, name=spec.name, position=spec.position)
        session.add(section)
        await session.flush()
        for shelf in spec.shelves:
            session.add(Shelf(
                section_id=section.id, code=shelf.code, side=shelf.side,
                position=shelf.position, levels_count=shelf.levels_count,
            ))
    await session.flush()
    logger.info("Andoza yaratildi: %s bo'lim", len(layout))
    return store.id


def side_label(side: str) -> str:
    return SIDE_LABELS.get(side, side)


def location_text(section_code: str, shelf_code: str, side: str, level: int) -> str:
    """Masalan: "A bo'lim → A3 javon (old tomon) → 5-qator"."""
    return f"{section_code} bo'lim → {shelf_code} javon ({side_label(side)}) → {level}-qator"


async def layout_view(session: AsyncSession, store_id: int) -> list[dict]:
    """WebApp xaritasi va bot menyusi uchun: bo'limlar, javonlar, bor/jami sonlar."""
    sections = await layout_repo.list_sections(session, store_id)
    counts = await layout_repo.shelf_stock_counts(session, store_id)
    view: list[dict] = []
    for section in sections:
        shelves = []
        for shelf in section.shelves:
            in_stock, total = counts.get(shelf.id, (0, 0))
            shelves.append({
                "id": shelf.id, "code": shelf.code, "side": shelf.side,
                "side_label": side_label(shelf.side), "position": shelf.position,
                "levels_count": shelf.levels_count, "in_stock": in_stock, "total": total,
            })
        view.append({"id": section.id, "code": section.code, "name": section.name, "shelves": shelves})
    return view
