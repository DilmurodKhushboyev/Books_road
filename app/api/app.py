"""FastAPI ilovasi: API routerlar, xato handlerlar, so'rov logi va WebApp statik fayllari."""
import logging
import time
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.ai.base import AIProvider
from app.api import routes_ai, routes_catalog
from app.api.errors import register_error_handlers
from app.config import Settings

logger = logging.getLogger("app.api")
WEBAPP_DIR = Path(__file__).resolve().parent.parent.parent / "webapp"
_SLOW_REQUEST_SECONDS = 2.0


def create_app(
    settings: Settings,
    ai: AIProvider,
    lifespan: Callable | None = None,
    extra_routers: list[APIRouter] | None = None,
) -> FastAPI:
    app = FastAPI(title="Books Road", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.state.settings = settings
    app.state.ai = ai
    register_error_handlers(app)

    @app.middleware("http")
    async def _log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - started
        if request.url.path.startswith("/api") or elapsed > _SLOW_REQUEST_SECONDS:
            level = logging.WARNING if elapsed > _SLOW_REQUEST_SECONDS else logging.INFO
            logger.log(level, "%s %s -> %s %.0fms", request.method, request.url.path,
                       response.status_code, elapsed * 1000)
        return response

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "ai": settings.ai_enabled}

    app.include_router(routes_catalog.router)
    app.include_router(routes_ai.router)
    for router in extra_routers or []:
        app.include_router(router)
    if WEBAPP_DIR.is_dir():
        app.mount("/", StaticFiles(directory=WEBAPP_DIR, html=True), name="webapp")
    return app
