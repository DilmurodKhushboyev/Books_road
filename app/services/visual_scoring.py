"""Rasm bo'yicha topishda nomzodlarni baholash (sof funksiyalar, testlanadi).

Signal manbalari:
  - matn: AI o'qigan nom/muallif  <->  bazadagi nom
  - rang: dominant hex ranglar + rang nomlari
  - tavsif: muqova rasmi/naqsh tavsifi
Nom o'qilmagan bo'lsa (past ishonch) — rang va tavsif og'irligi oshadi.
"""
from rapidfuzz import fuzz

from app.ai.base import DetectedItem
from app.constants import AI_LOW_CONFIDENCE
from app.services.image_utils import color_similarity
from app.services.text_normalize import normalize_text

_WEIGHTS_TITLE_READABLE = {"text": 0.6, "color": 0.2, "desc": 0.2}
_WEIGHTS_TITLE_UNREADABLE = {"text": 0.2, "color": 0.4, "desc": 0.4}
_KIND_MISMATCH_PENALTY = 0.5


def _color_names_overlap(first: list[str], second: list[str]) -> float:
    a = {normalize_text(c) for c in first if c}
    b = {normalize_text(c) for c in second if c}
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def score_candidate(query: DetectedItem, query_hex: list[str], row) -> float:
    """0..1 — nomzod rasmdagi narsaga qanchalik o'xshash."""
    query_text = normalize_text(f"{query.title} {query.author}")
    text = fuzz.token_set_ratio(query_text, row.search_norm) / 100 if query_text else 0.0
    color = max(
        color_similarity(query_hex, row.color_hex or []),
        _color_names_overlap(query.colors, row.colors or []),
    )
    query_desc = normalize_text(f"{query.shape} {query.visual_description}")
    row_desc = normalize_text(f"{row.shape} {row.visual_description}")
    desc = fuzz.token_set_ratio(query_desc, row_desc) / 100 if query_desc and row_desc else 0.0
    weights = _WEIGHTS_TITLE_READABLE if query.confidence >= AI_LOW_CONFIDENCE else _WEIGHTS_TITLE_UNREADABLE
    score = weights["text"] * text + weights["color"] * color + weights["desc"] * desc
    if query.kind and row.kind and query.kind != row.kind:
        score *= _KIND_MISMATCH_PENALTY
    return round(score, 4)


def rank_candidates(query: DetectedItem, query_hex: list[str], rows: list) -> list[tuple[float, object]]:
    unique = {row.id: row for row in rows}
    scored = [(score_candidate(query, query_hex, row), row) for row in unique.values()]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored


def candidate_payload(row) -> dict:
    """AI'ga qayta tanlash uchun yuboriladigan qisqa tavsif."""
    return {
        "title": row.title, "author": row.author, "colors": row.colors or [],
        "visual_description": row.visual_description,
    }
