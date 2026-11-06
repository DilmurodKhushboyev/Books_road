"""Nom bo'yicha qidiruv: normallashtirish -> SQL nomzodlar -> fuzzy reyting."""
import logging

from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    MAX_QUERY_LEN, MIN_QUERY_LEN, SEARCH_CANDIDATE_LIMIT, SEARCH_MIN_SCORE, SEARCH_RESULT_LIMIT,
)
from app.repositories import item_repo
from app.services.item_views import build_item_views
from app.services.text_normalize import normalize_text, search_tokens

logger = logging.getLogger(__name__)
_PREFIX_LEN = 4


class InvalidQuery(ValueError):
    """Qidiruv so'rovi juda qisqa yoki juda uzun."""


def validate_query(query: str | None) -> str:
    value = (query or "").strip()
    if len(value) > MAX_QUERY_LEN:
        raise InvalidQuery("too_long")
    if len(normalize_text(value)) < MIN_QUERY_LEN:
        raise InvalidQuery("too_short")
    return value


def score_text(query_norm: str, candidate_norm: str) -> float:
    """0..100: so'z tartibi, qisman moslik va xatolarga chidamli."""
    if not query_norm or not candidate_norm:
        return 0.0
    return max(
        fuzz.WRatio(query_norm, candidate_norm),
        fuzz.token_set_ratio(query_norm, candidate_norm),
    )


async def find_text_candidates(session: AsyncSession, store_id: int, query: str) -> list:
    tokens = search_tokens(query)
    rows = await item_repo.candidates_by_tokens(session, store_id, tokens, SEARCH_CANDIDATE_LIMIT)
    if rows:
        return rows
    # Imlo xatosi bo'lsa — so'z boshlari bo'yicha qayta urinamiz ("kunlr" -> "kunl")
    prefixes = list(dict.fromkeys(t[:_PREFIX_LEN] for t in tokens if len(t) > _PREFIX_LEN))
    return await item_repo.candidates_by_tokens(session, store_id, prefixes, SEARCH_CANDIDATE_LIMIT)


def rank_rows(query: str, rows: list, min_score: float = SEARCH_MIN_SCORE) -> dict[int, float]:
    query_norm = normalize_text(query)
    scores: dict[int, float] = {}
    for row in rows:
        score = score_text(query_norm, row.search_norm)
        if score >= min_score:
            scores[row.id] = score
    return scores


async def search_items(session: AsyncSession, store_id: int, query: str) -> list[dict]:
    query = validate_query(query)
    rows = await find_text_candidates(session, store_id, query)
    scores = rank_rows(query, rows)
    best_ids = sorted(scores, key=scores.get, reverse=True)[:SEARCH_RESULT_LIMIT]
    best_set = set(best_ids)
    best_rows = [row for row in rows if row.id in best_set]
    logger.info("search store=%s candidates=%s results=%s", store_id, len(rows), len(best_rows))
    return await build_item_views(session, best_rows, {i: scores[i] / 100 for i in best_ids})
