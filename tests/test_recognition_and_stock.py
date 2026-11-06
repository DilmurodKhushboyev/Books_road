import pytest

from app.db.session import session_scope
from app.repositories import layout_repo
from app.services import catalog_service, recognition_service, search_service
from app.services.access_service import AccessDenied
from app.services.batch_edits import BatchEdit
from app.services.recognition_service import RecognitionError
from tests.conftest import FakeAI, detected, make_ctx


async def _shelf_id(store_id):
    async with session_scope() as session:
        return (await layout_repo.list_sections(session, store_id))[1].shelves[6].id   # B7


async def test_recognize_edit_confirm_flow(db, photo_bytes):
    staff = await make_ctx(1001, staff=True)
    ai = FakeAI(detected=[
        detected("Sariq devni minib", "Xudoyberdi To'xtaboyev", conf=0.95, qty=2, box=[0, 0, 1000, 500]),
        detected("Noaniq kitob", conf=0.3),
        detected("Sariq devni minib", "Xudoyberdi To'xtaboyev", conf=0.9, qty=1),
    ])
    shelf_id = await _shelf_id(staff.store_id)
    batch = await recognition_service.recognize_shelf_photo(ai, staff, shelf_id, 4, photo_bytes)
    assert len(batch["items"]) == 3
    assert batch["items"][1]["low_confidence"] and not batch["items"][1]["include"]
    assert batch["items"][0]["thumb"].startswith("data:image/jpeg;base64,")

    # Past ishonchli elementni inson tuzatadi va yoqadi
    edited = await recognition_service.edit_batch(
        staff, batch["batch_id"], [BatchEdit(index=1, title="Ufq", author="Said Ahmad", include=True)])
    assert edited["items"][1]["title"] == "Ufq" and edited["items"][1]["include"]

    result = await recognition_service.confirm_batch(staff, batch["batch_id"])
    assert result == {"batch_id": batch["batch_id"], "saved": 3, "skipped": 0}

    async with session_scope() as session:
        found = await search_service.search_items(session, staff.store_id, "sariq devni minib")
    assert found[0]["placements"][0]["quantity"] == 3          # 2 + 1 bitta rasmdan qo'shildi
    assert found[0]["placements"][0]["location"].endswith("B7 javon (orqa tomon) → 4-qator")

    # Idempotentlik: ikkinchi tasdiqlash rad etiladi
    with pytest.raises(RecognitionError, match="batch_closed"):
        await recognition_service.confirm_batch(staff, batch["batch_id"])


async def test_customer_cannot_add_and_others_cannot_confirm(db, photo_bytes):
    customer = await make_ctx(2002)
    staff = await make_ctx(1001, staff=True)
    other_staff = await make_ctx(1002, staff=True)
    ai = FakeAI(detected=[detected("Kitob")])
    shelf_id = await _shelf_id(staff.store_id)
    with pytest.raises(AccessDenied):
        await recognition_service.recognize_shelf_photo(ai, customer, shelf_id, 1, photo_bytes)
    batch = await recognition_service.recognize_shelf_photo(ai, staff, shelf_id, 1, photo_bytes)
    with pytest.raises(RecognitionError, match="batch_not_found"):
        await recognition_service.confirm_batch(other_staff, batch["batch_id"])


async def test_bad_shelf_and_level_rejected_before_ai(db, photo_bytes):
    staff = await make_ctx(1001, staff=True)
    ai = FakeAI(detected=[detected("Kitob")])
    with pytest.raises(RecognitionError, match="shelf_not_found"):
        await recognition_service.recognize_shelf_photo(ai, staff, 99999, 1, photo_bytes)
    with pytest.raises(RecognitionError, match="bad_level"):
        await recognition_service.recognize_shelf_photo(ai, staff, await _shelf_id(staff.store_id), 9, photo_bytes)
    assert ai.calls == []


async def test_owner_from_admin_ids_and_stock_changes(db, photo_bytes):
    owner = await make_ctx(5005, admin_ids=frozenset({5005}))
    assert owner.is_owner and owner.can_edit
    batch = await recognition_service.recognize_shelf_photo(
        FakeAI(detected=[detected("Joynamoz yashil", kind="prayer_mat")]), owner,
        await _shelf_id(owner.store_id), 2, photo_bytes)
    await recognition_service.confirm_batch(owner, batch["batch_id"])
    async with session_scope() as session:
        view = (await search_service.search_items(session, owner.store_id, "joynamoz"))[0]
    pid = view["placements"][0]["placement_id"]
    async with session_scope() as session:
        placement = await catalog_service.change_stock(session, owner, pid, "dec")
        assert placement.quantity == 0 and placement.status == "out_of_stock"
        placement = await catalog_service.change_stock(session, owner, pid, "inc")
        assert placement.quantity == 1 and placement.status == "in_stock"
        with pytest.raises(catalog_service.CatalogError):
            await catalog_service.change_stock(session, owner, 99999, "inc")
    customer = await make_ctx(2002)
    async with session_scope() as session:
        with pytest.raises(AccessDenied):
            await catalog_service.change_stock(session, customer, pid, "out")
