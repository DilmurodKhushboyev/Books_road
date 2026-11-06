import httpx

from app.api.app import create_app
from app.config import Settings
from tests.conftest import FakeAI, detected, make_ctx
from tests.test_auth import TOKEN, make_init_data


def _client(ai=None):
    settings = Settings(bot_token=TOKEN, admin_telegram_ids="777", gemini_api_key="")
    app = create_app(settings, ai or FakeAI())
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _auth(user_id):
    return {"X-Telegram-Init-Data": make_init_data(user_id)}


async def test_health_and_unauthorized(db):
    async with _client() as client:
        assert (await client.get("/health")).json()["status"] == "ok"
        response = await client.get("/api/me")
        assert response.status_code == 401
        assert response.json()["error"] == "unauthorized"


async def test_me_layout_and_search(db):
    async with _client() as client:
        me = (await client.get("/api/me", headers=_auth(777))).json()
        assert me["is_owner"] and me["can_edit"]
        layout = (await client.get("/api/layout", headers=_auth(100))).json()
        assert len(layout["sections"]) == 2
        bad = await client.get("/api/search", params={"q": "a"}, headers=_auth(100))
        assert bad.status_code == 400 and "qisqa" in bad.json()["message"]


async def test_recognition_api_flow_and_permissions(db, photo_bytes):
    ai = FakeAI(detected=[detected("Shum bola", "G'afur G'ulom", conf=0.4)])
    await make_ctx(100)
    async with _client(ai) as client:
        files = {"photo": ("p.jpg", photo_bytes, "image/jpeg")}
        denied = await client.post("/api/recognitions", data={"shelf_id": 1, "level": 1}, files=files,
                                   headers=_auth(100))
        assert denied.status_code == 403
        created = await client.post("/api/recognitions", data={"shelf_id": 1, "level": 2}, files=files,
                                    headers=_auth(777))
        assert created.status_code == 200
        batch = created.json()
        assert batch["items"][0]["low_confidence"]
        edits = {"edits": [{"index": 0, "include": True, "quantity": 4}]}
        confirmed = await client.post(f"/api/recognitions/{batch['batch_id']}/confirm", json=edits, headers=_auth(777))
        assert confirmed.json()["saved"] == 1
        again = await client.post(f"/api/recognitions/{batch['batch_id']}/confirm", json=edits, headers=_auth(777))
        assert again.status_code == 409
        found = (await client.get("/api/search", params={"q": "shum bola"}, headers=_auth(100))).json()
        place = found["results"][0]["placements"][0]
        assert place["quantity"] == 4 and place["shelf_code"] == "A1" and place["level"] == 2
        stock = await client.post(f"/api/placements/{place['placement_id']}/stock", json={"action": "out"},
                                  headers=_auth(100))
        assert stock.status_code == 403
        thumb = await client.get(f"/api/items/{found['results'][0]['item_id']}/thumb", headers=_auth(100))
        assert thumb.status_code == 200 and thumb.headers["content-type"] == "image/jpeg"


async def test_invalid_image_rejected(db):
    async with _client(FakeAI(detected=[detected("X")])) as client:
        files = {"photo": ("p.jpg", b"not an image", "image/jpeg")}
        response = await client.post("/api/recognitions", data={"shelf_id": 1, "level": 1}, files=files,
                                     headers=_auth(777))
        assert response.status_code == 400 and response.json()["error"] == "invalid_image"
