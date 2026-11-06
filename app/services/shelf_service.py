"""Javon ichini ko'rish: qaysi qatorda nimalar bor (bot va WebApp uchun umumiy)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import KIND_LABELS, STATUS_IN_STOCK
from app.repositories import item_repo, layout_repo
from app.services.layout_service import side_label


class ShelfNotFound(LookupError):
    """Javon topilmadi yoki boshqa do'konga tegishli."""


async def shelf_contents(
    session: AsyncSession, store_id: int, shelf_id: int, level: int | None = None
) -> dict:
    shelf = await layout_repo.get_shelf(session, store_id, shelf_id)
    if shelf is None:
        raise ShelfNotFound(shelf_id)
    if level is not None and not 1 <= level <= shelf.levels_count:
        raise ShelfNotFound(shelf_id)
    rows = await item_repo.items_on_shelf(session, shelf.id, level)
    levels: dict[int, list[dict]] = {lvl: [] for lvl in range(1, shelf.levels_count + 1)}
    for row in rows:
        levels.setdefault(row.level, []).append({
            "placement_id": row.placement_id, "item_id": row.item_id,
            "title": row.title, "author": row.author,
            "kind_label": KIND_LABELS.get(row.kind, row.kind),
            "quantity": row.quantity, "in_stock": row.status == STATUS_IN_STOCK,
        })
    selected = [level] if level is not None else sorted(levels)
    return {
        "shelf_id": shelf.id, "code": shelf.code, "side": shelf.side,
        "side_label": side_label(shelf.side), "section_code": shelf.section.code,
        "levels_count": shelf.levels_count,
        "levels": [{"level": lvl, "items": levels.get(lvl, [])} for lvl in selected],
    }
