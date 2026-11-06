"""WebApp API: rasm orqali javonga qo'shish va rasm bo'yicha topish (AI)."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.api.auth import current_context
from app.api.schemas import BatchEditsIn
from app.constants import MAX_PHOTO_BYTES, MAX_SHELF_LEVELS
from app.services import recognition_service, visual_match_service
from app.services.access_service import UserContext, require_editor
from app.services.image_utils import InvalidImage
from app.services.rate_limit import ai_limiter

router = APIRouter(prefix="/api")


async def _read_photo(photo: UploadFile) -> bytes:
    data = await photo.read(MAX_PHOTO_BYTES + 1)
    if len(data) > MAX_PHOTO_BYTES:
        raise InvalidImage("too_big")
    return data


def _check_ai_rate(ctx: UserContext) -> None:
    if not ai_limiter.allow(ctx.telegram_id):
        raise HTTPException(status_code=429, detail="rate_limited")


@router.post("/recognitions")
async def create_recognition(
    request: Request,
    shelf_id: int = Form(...),
    level: int = Form(..., ge=1, le=MAX_SHELF_LEVELS),
    photo: UploadFile = File(...),
    ctx: UserContext = Depends(current_context),
) -> dict:
    require_editor(ctx)
    _check_ai_rate(ctx)
    data = await _read_photo(photo)
    return await recognition_service.recognize_shelf_photo(
        request.app.state.ai, ctx, shelf_id, level, data
    )


@router.get("/recognitions/{batch_id}")
async def get_recognition(batch_id: int, ctx: UserContext = Depends(current_context)) -> dict:
    return await recognition_service.get_batch(ctx, batch_id)


@router.post("/recognitions/{batch_id}/edit")
async def edit_recognition(batch_id: int, body: BatchEditsIn,
                           ctx: UserContext = Depends(current_context)) -> dict:
    return await recognition_service.edit_batch(ctx, batch_id, body.to_domain())


@router.post("/recognitions/{batch_id}/confirm")
async def confirm_recognition(batch_id: int, body: BatchEditsIn,
                              ctx: UserContext = Depends(current_context)) -> dict:
    return await recognition_service.confirm_batch(ctx, batch_id, body.to_domain())


@router.post("/recognitions/{batch_id}/cancel")
async def cancel_recognition(batch_id: int, ctx: UserContext = Depends(current_context)) -> dict:
    await recognition_service.cancel_batch(ctx, batch_id)
    return {"ok": True}


@router.post("/find-by-photo")
async def find_by_photo(request: Request, photo: UploadFile = File(...),
                        ctx: UserContext = Depends(current_context)) -> dict:
    _check_ai_rate(ctx)
    data = await _read_photo(photo)
    return await visual_match_service.find_by_photo(request.app.state.ai, ctx, data)
