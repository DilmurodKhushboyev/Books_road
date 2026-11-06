"""Domen xatolarini xavfsiz HTTP javoblarga aylantirish (ichki tafsilot chiqmaydi)."""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.ai.base import AIError, AIUnavailable
from app.services.access_service import AccessDenied
from app.services.catalog_service import CatalogError
from app.services.image_utils import InvalidImage
from app.services.recognition_service import RecognitionError
from app.services.search_service import InvalidQuery
from app.services.shelf_service import ShelfNotFound
from app.texts import error_text

logger = logging.getLogger(__name__)


def _response(status: int, code: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": error_text(code)})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http(_: Request, exc: HTTPException) -> JSONResponse:
        code = exc.detail if isinstance(exc.detail, str) else "internal"
        return _response(exc.status_code, code)

    @app.exception_handler(AccessDenied)
    async def _denied(_: Request, exc: AccessDenied) -> JSONResponse:
        return _response(403, "forbidden")

    @app.exception_handler(InvalidQuery)
    async def _query(_: Request, exc: InvalidQuery) -> JSONResponse:
        return _response(400, str(exc))

    @app.exception_handler(InvalidImage)
    async def _image(_: Request, exc: InvalidImage) -> JSONResponse:
        return _response(400, "invalid_image")

    @app.exception_handler(RecognitionError)
    async def _recognition(_: Request, exc: RecognitionError) -> JSONResponse:
        code = str(exc)
        return _response(409 if code == "batch_closed" else 400, code)

    @app.exception_handler(CatalogError)
    async def _catalog(_: Request, exc: CatalogError) -> JSONResponse:
        code = str(exc)
        return _response(404 if code == "not_found" else 400, code)

    @app.exception_handler(ShelfNotFound)
    async def _shelf(_: Request, exc: ShelfNotFound) -> JSONResponse:
        return _response(404, "shelf_not_found")

    @app.exception_handler(AIUnavailable)
    async def _ai_off(_: Request, exc: AIUnavailable) -> JSONResponse:
        return _response(503, "ai_unavailable")

    @app.exception_handler(AIError)
    async def _ai(_: Request, exc: AIError) -> JSONResponse:
        logger.warning("AI xatosi: %s", exc)
        return _response(502, "ai_error")

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Kutilmagan xato: %s %s", request.method, request.url.path)
        return _response(500, "internal")
