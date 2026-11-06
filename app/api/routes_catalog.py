"""WebApp API: profil, xarita, javon, qidiruv, qoldiq. Handler faqat servisni chaqiradi."""
from fastapi import APIRouter, Depends, Query, Response

from app.api.auth import current_context
from app.api.schemas import StockIn
from app.constants import KIND_LABELS, LEVEL_NUMBERING_HINT, MAX_QUERY_LEN
from app.db.session import session_scope
from app.repositories import item_repo
from app.services import catalog_service, layout_service, search_service, shelf_service
from app.services.access_service import UserContext
from app.services.item_views import build_item_views

router = APIRouter(prefix="/api")
_THUMB_CACHE_SECONDS = 3600


@router.get("/me")
async def me(ctx: UserContext = Depends(current_context)) -> dict:
    return {
        "user_id": ctx.user_id, "role": ctx.role, "can_edit": ctx.can_edit,
        "is_owner": ctx.is_owner, "kinds": KIND_LABELS, "level_hint": LEVEL_NUMBERING_HINT,
    }


@router.get("/layout")
async def layout(ctx: UserContext = Depends(current_context)) -> dict:
    async with session_scope() as session:
        return {"sections": await layout_service.layout_view(session, ctx.store_id)}


@router.get("/shelves/{shelf_id}")
async def shelf(shelf_id: int, level: int | None = Query(default=None, ge=1),
                ctx: UserContext = Depends(current_context)) -> dict:
    async with session_scope() as session:
        return await shelf_service.shelf_contents(session, ctx.store_id, shelf_id, level)


@router.get("/search")
async def search(q: str = Query(default="", max_length=MAX_QUERY_LEN),
                 ctx: UserContext = Depends(current_context)) -> dict:
    async with session_scope() as session:
        return {"results": await search_service.search_items(session, ctx.store_id, q)}


@router.get("/items/{item_id}/thumb")
async def item_thumb(item_id: int, ctx: UserContext = Depends(current_context)) -> Response:
    async with session_scope() as session:
        data = await item_repo.get_thumbnail(session, ctx.store_id, item_id)
    if data is None:
        return Response(status_code=404)
    return Response(content=data, media_type="image/jpeg",
                    headers={"Cache-Control": f"private, max-age={_THUMB_CACHE_SECONDS}"})


@router.post("/placements/{placement_id}/stock")
async def change_stock(placement_id: int, body: StockIn,
                       ctx: UserContext = Depends(current_context)) -> dict:
    async with session_scope() as session:
        placement = await catalog_service.change_stock(session, ctx, placement_id, body.action)
        item = await item_repo.get_item(session, ctx.store_id, placement.item_id)
        views = await build_item_views(session, [item], {item.id: 1.0})
    return views[0]
