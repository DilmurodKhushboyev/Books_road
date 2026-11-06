import pytest

from app.db.session import session_scope
from app.repositories import layout_repo
from app.services import layout_service, search_service, shelf_service
from app.services.catalog_service import ItemInput, place_item, upsert_item
from app.services.search_service import InvalidQuery


async def _first_shelf(store_id):
    async with session_scope() as session:
        sections = await layout_repo.list_sections(session, store_id)
        return sections[0].shelves[2]   # A3


async def _add(store_id, title, author="", level=5, quantity=2):
    shelf = await _first_shelf(store_id)
    async with session_scope() as session:
        item = await upsert_item(session, store_id, None, ItemInput(title=title, author=author))
        return await place_item(session, item.id, shelf.id, level, quantity, None)


async def test_default_layout_20_shelves_idempotent(db):
    async with session_scope() as session:
        store_id = await layout_service.ensure_default_store(session)
        again = await layout_service.ensure_default_store(session)
        view = await layout_service.layout_view(session, store_id)
    assert store_id == again
    assert [s["code"] for s in view] == ["A", "B"]
    assert sum(len(s["shelves"]) for s in view) == 20
    sides = [sh["side"] for sh in view[0]["shelves"]]
    assert sides.count("front") == 5 and sides.count("back") == 5
    assert all(sh["levels_count"] == 8 for s in view for sh in s["shelves"])


async def test_search_cyrillic_finds_latin_with_location(db):
    async with session_scope() as session:
        store_id = await layout_service.ensure_default_store(session)
    await _add(store_id, "O'tgan kunlar", "Abdulla Qodiriy")
    async with session_scope() as session:
        results = await search_service.search_items(session, store_id, "Ўтган кунлар")
    assert results and results[0]["title"] == "O'tgan kunlar"
    place = results[0]["placements"][0]
    assert place["location"] == "A bo'lim → A3 javon (old tomon) → 5-qator"
    assert results[0]["in_stock"] is True and place["quantity"] == 2


async def test_search_typo_and_author(db):
    async with session_scope() as session:
        store_id = await layout_service.ensure_default_store(session)
    await _add(store_id, "Mehrobdan chayon", "Abdulla Qodiriy")
    async with session_scope() as session:
        typo = await search_service.search_items(session, store_id, "mehrobdn chayn")
        by_author = await search_service.search_items(session, store_id, "qodiriy")
    assert typo and typo[0]["title"] == "Mehrobdan chayon"
    assert by_author and by_author[0]["title"] == "Mehrobdan chayon"


async def test_search_nothing_and_invalid(db):
    async with session_scope() as session:
        store_id = await layout_service.ensure_default_store(session)
        assert await search_service.search_items(session, store_id, "mavjud emas kitob") == []
        with pytest.raises(InvalidQuery):
            await search_service.search_items(session, store_id, "a")
        with pytest.raises(InvalidQuery):
            await search_service.search_items(session, store_id, "x" * 500)


async def test_duplicate_item_not_created(db):
    async with session_scope() as session:
        store_id = await layout_service.ensure_default_store(session)
        first = await upsert_item(session, store_id, None, ItemInput(title="Kecha va kunduz", author="Cho'lpon"))
        second = await upsert_item(session, store_id, None, ItemInput(title="КЕЧА ВА КУНДУЗ", author="Чўлпон"))
    assert first.id == second.id


async def test_shelf_contents_and_bad_level(db):
    async with session_scope() as session:
        store_id = await layout_service.ensure_default_store(session)
    await _add(store_id, "Alkimyogar", level=1)
    shelf = await _first_shelf(store_id)
    async with session_scope() as session:
        contents = await shelf_service.shelf_contents(session, store_id, shelf.id)
        assert len(contents["levels"]) == 8
        assert contents["levels"][0]["items"][0]["title"] == "Alkimyogar"
        with pytest.raises(shelf_service.ShelfNotFound):
            await shelf_service.shelf_contents(session, store_id, shelf.id, level=9)
        with pytest.raises(shelf_service.ShelfNotFound):
            await shelf_service.shelf_contents(session, store_id, 99999)
