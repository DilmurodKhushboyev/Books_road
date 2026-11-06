from types import SimpleNamespace

from app.ai.base import MatchChoice
from app.bot import formatters
from app.services import recognition_service, visual_match_service
from app.services.rate_limit import RateLimiter
from app.services.visual_scoring import rank_candidates
from tests.conftest import FakeAI, detected, make_ctx


def _row(item_id, title, colors, hexes, desc, kind="book"):
    return SimpleNamespace(id=item_id, title=title, author="", kind=kind, search_norm=title.lower(),
                           colors=colors, color_hex=hexes, shape="kitob", visual_description=desc)


def test_readable_title_wins():
    rows = [_row(1, "ufq", ["qizil"], ["#cc2222"], "qizil muqova"),
            _row(2, "alkimyogar", ["ko'k"], ["#2233aa"], "ko'k muqova")]
    query = detected("Alkimyogar", conf=0.9, colors=["qizil"])
    assert rank_candidates(query, ["#cc2222"], rows)[0][1].id == 2


def test_unreadable_title_uses_color_and_description():
    rows = [_row(1, "ufq", ["qizil"], ["#cc2222"], "qizil muqova oltin harflar"),
            _row(2, "alkimyogar", ["ko'k"], ["#2233aa"], "ko'k muqova sahro rasmi")]
    query = detected("???", conf=0.1, colors=["ko'k"])
    query.visual_description = "ko'k muqova sahro rasmi"
    assert rank_candidates(query, ["#2233aa"], rows)[0][1].id == 2


def test_kind_mismatch_penalized():
    rows = [_row(1, "oud", [], [], "", kind="perfume"), _row(2, "oud", [], [], "", kind="book")]
    ranked = rank_candidates(detected("Oud", kind="perfume"), [], rows)
    assert ranked[0][1].id == 1 and ranked[0][0] > ranked[1][0]


def test_rate_limiter_window():
    limiter = RateLimiter(limit=2, window=60)
    assert limiter.allow(1, now=0) and limiter.allow(1, now=1)
    assert not limiter.allow(1, now=2)
    assert limiter.allow(2, now=2)              # boshqa foydalanuvchi alohida
    assert limiter.allow(1, now=61)             # oyna o'tdi


def test_bot_formatter_escapes_html():
    view = {"title": "<b>X</b>", "author": "A&B", "kind_label": "📚 Kitob", "placements": []}
    text = formatters.search_results("<script>", [view])
    assert "<script>" not in text and "&lt;b&gt;X&lt;/b&gt;" in text and "A&amp;B" in text


async def test_find_by_photo_end_to_end(db, photo_bytes):
    staff = await make_ctx(1001, staff=True)
    batch = await recognition_service.recognize_shelf_photo(
        FakeAI(detected=[detected("Ikki eshik orasi", "O'tkir Hoshimov"), detected("Dunyoning ishlari")]),
        staff, 1, 3, photo_bytes)
    await recognition_service.confirm_batch(staff, batch["batch_id"])

    customer = await make_ctx(3003)
    ai = FakeAI(described=detected("IKKI ESHIK ORASI", "Hoshimov", conf=0.9))
    result = await visual_match_service.find_by_photo(ai, customer, photo_bytes)
    assert result["recognized"] and result["confident"]
    assert result["results"][0]["title"] == "Ikki eshik orasi"
    assert result["results"][0]["placements"][0]["level"] == 3


async def test_find_by_photo_unsure_uses_ai_rerank(db, photo_bytes):
    staff = await make_ctx(1001, staff=True)
    batch = await recognition_service.recognize_shelf_photo(
        FakeAI(detected=[detected("Qora kitob", colors=["qora"]), detected("Oq kema", colors=["oq"])]),
        staff, 1, 1, photo_bytes)
    await recognition_service.confirm_batch(staff, batch["batch_id"])
    ai = FakeAI(described=detected("noma'lum", conf=0.1, colors=["ko'k"]),
                choice=MatchChoice(index=1, confidence=0.9))
    result = await visual_match_service.find_by_photo(ai, staff, photo_bytes)
    assert "choose" in ai.calls
    assert result["results"][0]["score"] == 0.9


async def test_find_by_photo_not_recognized(db, photo_bytes):
    customer = await make_ctx(3003)
    result = await visual_match_service.find_by_photo(FakeAI(described=None), customer, photo_bytes)
    assert result == {"recognized": False, "query": None, "confident": False, "results": []}
