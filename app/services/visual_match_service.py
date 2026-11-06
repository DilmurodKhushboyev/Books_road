"""Rasm bo'yicha topish: AI tavsifi -> nomzodlar -> baholash -> (kerak bo'lsa) AI qayta tanlovi."""
import asyncio
import logging

from app.ai.base import AIError, AIProvider, DetectedItem
from app.constants import (
    VISUAL_CANDIDATE_LIMIT, VISUAL_CONFIDENT_SCORE, VISUAL_MIN_SCORE, VISUAL_TIE_MARGIN,
    VISUAL_TOP_FOR_RERANK,
)
from app.db.session import session_scope
from app.repositories import item_repo
from app.services import image_utils
from app.services.access_service import UserContext
from app.services.item_views import build_item_views
from app.services.search_service import find_text_candidates
from app.services.visual_scoring import candidate_payload, rank_candidates

logger = logging.getLogger(__name__)
_RESULT_LIMIT = 5
_RERANK_MIN_CONFIDENCE = 0.5


def _prepare(photo: bytes) -> tuple[object, bytes]:
    image = image_utils.load_image(photo)
    return image, image_utils.prepare_for_ai(image)


def _query_colors(image, box: list[int] | None) -> list[str]:
    return image_utils.dominant_colors(image_utils.crop_box(image, box))


async def _load_candidates(store_id: int, query: DetectedItem) -> list:
    async with session_scope() as session:
        rows = []
        text = f"{query.title} {query.author}".strip()
        if text:
            rows += await find_text_candidates(session, store_id, text)
        rows += await item_repo.candidates_by_kind(session, store_id, query.kind, VISUAL_CANDIDATE_LIMIT)
        return rows


def is_confident(ranked: list) -> bool:
    """Eng yaxshi ball yuqori VA ikkinchisidan aniq ajralib turishi kerak (teng bo'lsa — noaniq)."""
    if not ranked or ranked[0][0] < VISUAL_CONFIDENT_SCORE:
        return False
    return len(ranked) == 1 or ranked[0][0] - ranked[1][0] >= VISUAL_TIE_MARGIN


async def _rerank(ai: AIProvider, ai_bytes: bytes, ranked: list) -> list:
    """Eng yaxshi natija ishonchsiz bo'lsa — AI'dan nomzodlar orasidan tanlashni so'raymiz."""
    top = ranked[:VISUAL_TOP_FOR_RERANK]
    try:
        choice = await ai.choose_match(ai_bytes, [candidate_payload(row) for _, row in top])
    except AIError as exc:
        logger.warning("Qayta tanlov ishlamadi: %s", exc)
        return ranked
    if choice.index is None or choice.confidence < _RERANK_MIN_CONFIDENCE:
        return ranked
    chosen_score, chosen_row = top[choice.index]
    boosted = (max(chosen_score, choice.confidence), chosen_row)
    return [boosted] + [pair for pair in ranked if pair[1].id != chosen_row.id]


async def find_by_photo(ai: AIProvider, ctx: UserContext, photo: bytes) -> dict:
    image, ai_bytes = await asyncio.to_thread(_prepare, photo)
    query = await ai.describe_item(ai_bytes)
    if query is None:
        return {"recognized": False, "query": None, "confident": False, "results": []}
    query_hex = await asyncio.to_thread(_query_colors, image, query.box)
    rows = await _load_candidates(ctx.store_id, query)
    ranked = rank_candidates(query, query_hex, rows)
    if ranked and not is_confident(ranked):
        ranked = await _rerank(ai, ai_bytes, ranked)
    best = [(score, row) for score, row in ranked if score >= VISUAL_MIN_SCORE][:_RESULT_LIMIT]
    async with session_scope() as session:
        views = await build_item_views(session, [row for _, row in best], {row.id: s for s, row in best})
    confident = is_confident(best)
    logger.info("photo-find user=%s candidates=%s results=%s confident=%s",
                ctx.user_id, len(rows), len(views), confident)
    return {
        "recognized": True,
        "query": {"title": query.title, "author": query.author, "kind": query.kind,
                  "colors": query.colors, "confidence": round(query.confidence, 2)},
        "confident": confident,
        "results": views,
    }
