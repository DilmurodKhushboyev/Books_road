"""Telegram WebApp initData tekshiruvi (HMAC-SHA256) va foydalanuvchi konteksti.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, Request

from app.constants import INIT_DATA_MAX_AGE_SECONDS
from app.db.session import session_scope
from app.services.access_service import UserContext, resolve_context
from app.services.rate_limit import general_limiter

logger = logging.getLogger(__name__)


class InvalidInitData(ValueError):
    pass


def validate_init_data(init_data: str, bot_token: str, max_age: int = INIT_DATA_MAX_AGE_SECONDS,
                       now: float | None = None) -> dict:
    """To'g'ri bo'lsa Telegram user dict'ini qaytaradi, aks holda InvalidInitData."""
    if not init_data or not bot_token:
        raise InvalidInitData("empty")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received_hash = pairs.pop("hash", "")
    if not received_hash:
        raise InvalidInitData("no_hash")
    check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise InvalidInitData("bad_hash")
    try:
        auth_date = int(pairs.get("auth_date", "0"))
        user = json.loads(pairs.get("user", "{}"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise InvalidInitData("bad_payload") from exc
    current = time.time() if now is None else now
    if current - auth_date > max_age:
        raise InvalidInitData("expired")
    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        raise InvalidInitData("no_user")
    return user


async def current_context(
    request: Request, x_telegram_init_data: str = Header(default="")
) -> UserContext:
    settings = request.app.state.settings
    try:
        tg_user = validate_init_data(x_telegram_init_data, settings.bot_token)
    except InvalidInitData as exc:
        logger.info("WebApp auth rad etildi: %s", exc)
        raise HTTPException(status_code=401, detail="unauthorized") from exc
    if not general_limiter.allow(tg_user["id"]):
        raise HTTPException(status_code=429, detail="rate_limited")
    full_name = " ".join(filter(None, [tg_user.get("first_name"), tg_user.get("last_name")]))
    async with session_scope() as session:
        ctx = await resolve_context(session, tg_user["id"], full_name, tg_user.get("username"),
                                    settings.admin_ids)
    if ctx.is_blocked:
        raise HTTPException(status_code=403, detail="forbidden")
    return ctx
