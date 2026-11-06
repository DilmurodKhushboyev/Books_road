"""Mahsulot + joylashuvlarini yagona ko'rinishga (dict) aylantirish.

Qidiruv, rasm bo'yicha topish va javon ko'rish — hammasi shu formatni qaytaradi,
shuning uchun bot va WebApp bir xil ma'lumot ko'radi.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import KIND_LABELS, STATUS_IN_STOCK
from app.repositories import item_repo
from app.services.layout_service import location_text, side_label


def placement_view(row) -> dict:
    return {
        "placement_id": row.id,
        "shelf_id": row.shelf_id,
        "section_code": row.section_code,
        "shelf_code": row.shelf_code,
        "side": row.side,
        "side_label": side_label(row.side),
        "level": row.level,
        "quantity": row.quantity,
        "status": row.status,
        "in_stock": row.status == STATUS_IN_STOCK,
        "location": location_text(row.section_code, row.shelf_code, row.side, row.level),
    }


async def build_item_views(session: AsyncSession, rows: list, scores: dict[int, float]) -> list[dict]:
    """rows — item_repo ustunlari (id, kind, title, author...). Tartib scores bo'yicha."""
    item_ids = [row.id for row in rows]
    placements = await item_repo.placements_for_items(session, item_ids)
    by_item: dict[int, list[dict]] = {}
    for row in placements:
        by_item.setdefault(row.item_id, []).append(placement_view(row))
    views = []
    for row in rows:
        item_placements = by_item.get(row.id, [])
        views.append({
            "item_id": row.id,
            "title": row.title,
            "author": row.author,
            "kind": row.kind,
            "kind_label": KIND_LABELS.get(row.kind, row.kind),
            "score": round(scores.get(row.id, 0.0), 2),
            "in_stock": any(p["in_stock"] for p in item_placements),
            "placements": item_placements,
        })
    views.sort(key=lambda view: view["score"], reverse=True)
    return views
