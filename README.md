# 📚 Books Road — Telegram bot + WebApp

**Maqsad:** kitob (yoki atir, joynamoz, istalgan narsa) nomini yozish yoki rasmini yuborish orqali
uning **qaysi bo'lim → qaysi javon → qaysi qatorda** turganini yoki **qolmaganini** aniq bilish.

Xodim javonning bir qatorini suratga oladi → bepul AI (Google Gemini) undagi barcha narsalarni
o'qiydi (nom, muallif, rang, shakl, muqova rasmi) → xodim tasdiqlaydi → bazaga yoziladi.
Keyin istalgan mijoz nom yozib yoki rasm yuborib topadi.

---

## 🏬 Do'kon andozasi (PDF obmer rejasi, 77.9 m²)

```
            ┌──────── A bo'lim ────────┐   ┌──────── B bo'lim ────────┐
            │ old tomon │ orqa tomon   │   │ old tomon │ orqa tomon   │
            │   ⬆️A1    │   ⬇️A6       │   │   ⬆️B1    │   ⬇️B6       │
            │   ⬆️A2    │   ⬇️A7       │   │   ⬆️B2    │   ⬇️B7       │
            │   ⬆️A3    │   ⬇️A8       │   │   ⬆️B3    │   ⬇️B8       │
            │   ⬆️A4    │   ⬇️A9       │   │   ⬆️B4    │   ⬇️B9       │
            │   ⬆️A5    │   ⬇️A10      │   │   ⬆️B5    │   ⬇️B10      │
            └──────────────────────────┘   └──────────────────────────┘
                                   🚪 Kirish
```
- 2 bo'lim × 10 javon = **20 javon**, har birida **8 qator** (1-qator — eng yuqori).
- Andoza kodda emas, konfiguratsiyada: `app/layout/default_layout.py`. Boshqa do'kon/javon soni
  uchun faqat shu fayl o'zgaradi. Har bir javonning qator soni alohida (`levels_count`).

## 🧩 Imkoniyatlar

| Imkoniyat | Bot | WebApp | Kim |
|---|---|---|---|
| Nom bo'yicha qidirish (kirill ⇄ lotin, apostrof, imlo xatolari) | matn yozish | 🔎 Qidiruv | hamma |
| Rasm bo'yicha topish (nom + rang + muqova tavsifi + AI qayta tanlovi) | rasm yuborish | 📷 Rasm | hamma |
| Do'kon xaritasi, javon ichidagi qatorlar | 🗄 Javonlarni ko'rish | 🗺 Xarita | hamma |
| Javon rasmidan narsalarni kiritish (tahrir + tasdiqlash) | ➕ Javonga qo'shish | ➕ Qo'shish | xodim |
| Qoldiq: ➖ / ➕ / ❌ Qolmadi | natija ostidagi tugmalar | kartochkada | xodim |
| Xodim qo'shish | `/add_staff <ID>` | — | egasi |

Turlar: kitob, attorlik, joynamoz, kanselyariya, sovg'a, boshqa (`app/constants.py → KIND_LABELS`).

---

## 🗺 BOT XARITASI (fayllar va ularning vazifasi)

> Har bir fayl **bitta** vazifaga javobgar. O'zgartirish kerak bo'lsa — shu jadvaldan faylni toping.

### Ishga tushirish va sozlash
| Fayl | Vazifasi |
|---|---|
| `app/main.py` | Kirish nuqtasi: baza → do'kon andozasi → AI → bot (polling/webhook) + WebApp API |
| `app/config.py` | Env o'zgaruvchilari (yagona eshik). `postgresql://` → async drayver |
| `app/constants.py` | Barcha limitlar, chegaralar, rollar, turlar, holatlar (magic number yo'q) |
| `app/texts.py` | Xato xabarlari — bot va WebApp uchun **umumiy** |
| `app/logging_setup.py` | Log formati |
| `app/layout/default_layout.py` | Do'kon andozasi (bo'limlar, javonlar, qatorlar) |

### Baza
| Fayl | Vazifasi |
|---|---|
| `app/db/models.py` | ORM: User, Store, StoreMember, Section, Shelf, Item, Placement, ItemImage, RecognitionBatch |
| `app/db/session.py` | Engine va `session_scope()` (commit/rollback) |
| `migrations/versions/0001_initial.py` | Boshlang'ich sxema (+ Postgres'da `pg_trgm` indeks) |
| `app/repositories/user_repo.py` | Foydalanuvchi, rol so'rovlari |
| `app/repositories/layout_repo.py` | Do'kon, bo'lim, javon, javon bo'yicha sonlar (GROUP BY) |
| `app/repositories/item_repo.py` | Mahsulot, joylashuv, kichik rasm so'rovlari |
| `app/repositories/batch_repo.py` | Tasdiqlanmagan AI ro'yxatlari, atomik `claim_batch` (idempotentlik) |

### Biznes-mantiq (servislar) — bot ham, WebApp ham **shularni** chaqiradi
| Fayl | Vazifasi |
|---|---|
| `app/services/access_service.py` | `UserContext`, rollar (egasi/xodim/mijoz), `require_editor`, `grant_staff` |
| `app/services/layout_service.py` | Andozani yaratish (idempotent), joylashuv matni, xarita ko'rinishi |
| `app/services/shelf_service.py` | Javon ichini qatorlar bo'yicha ko'rish |
| `app/services/text_normalize.py` | Kirill→lotin, apostroflar, normallashtirish |
| `app/services/search_service.py` | Nom bo'yicha qidiruv (SQL nomzod + fuzzy reyting) |
| `app/services/item_views.py` | Mahsulot+joylashuvlar → yagona dict (bot va WebApp bir xil ko'radi) |
| `app/services/catalog_service.py` | Mahsulotni dublikatsiz saqlash, joylashtirish, qoldiq amallari |
| `app/services/recognition_service.py` | Javon rasmi → AI → ro'yxat → tahrir → tasdiqlash/bekor |
| `app/services/batch_edits.py` | Ro'yxat elementlarini tahrirlash va ko'rinishi (sof funksiyalar) |
| `app/services/visual_match_service.py` | Rasm bo'yicha topish jarayoni |
| `app/services/visual_scoring.py` | Nomzodlarni matn/rang/tavsif bo'yicha baholash |
| `app/services/image_utils.py` | Rasm tekshirish, kichraytirish, kesish, dominant ranglar |
| `app/services/rate_limit.py` | Rate limit (umumiy va AI uchun) |

### AI
| Fayl | Vazifasi |
|---|---|
| `app/ai/base.py` | AI interfeysi (eshik): `detect_items`, `describe_item`, `choose_match` |
| `app/ai/gemini.py` | Gemini REST implementatsiyasi (retry, timeout, parallel cheklov) |
| `app/ai/prompts.py` | Promptlar va JSON sxemalar |
| `app/ai/parsing.py` | AI javobini validatsiya (noto'g'ri JSON bazaga tushmaydi) |
| `app/ai/factory.py` | Provayder tanlash; kalit yo'q bo'lsa `DisabledAI` |

### Telegram bot
| Fayl | Vazifasi |
|---|---|
| `app/bot/setup.py` | Dispatcher, middleware'lar, routerlar tartibi |
| `app/bot/middlewares.py` | Rate limit + `ctx` (foydalanuvchi konteksti) |
| `app/bot/webhook.py` | Webhook rejimi (FastAPI orqali) |
| `app/bot/texts.py` | Bot matnlari va tugma nomlari |
| `app/bot/keyboards.py` | Reply/inline klaviaturalar |
| `app/bot/callbacks.py` | Inline tugma ma'lumotlari (NavCb, BatchCb, StockCb) |
| `app/bot/states.py` | FSM holatlari (AddFlow, FindFlow) |
| `app/bot/formatters.py` | Natijalarni HTML matnga (hammasi escape qilinadi) |
| `app/bot/photo_io.py` | Rasmni xavfsiz yuklab olish |
| `app/bot/handlers/start.py` | /start, /help, /myid, /add_staff |
| `app/bot/handlers/browse.py` | Bo'lim → javon → qator navigatsiyasi (ko'rish va qo'shish) |
| `app/bot/handlers/add_items.py` | Javon rasmi → ko'rib chiqish → tasdiqlash |
| `app/bot/handlers/find_photo.py` | Rasm bo'yicha topish |
| `app/bot/handlers/search.py` | Matn qidiruvi + qoldiq tugmalari (eng oxirgi router) |
| `app/bot/handlers/errors.py` | Global xato handler (ichki tafsilot foydalanuvchiga chiqmaydi) |

### WebApp API (FastAPI)
| Fayl | Endpointlar |
|---|---|
| `app/api/app.py` | Ilova, so'rov logi, `/health`, statik WebApp |
| `app/api/auth.py` | Telegram `initData` HMAC tekshiruvi → `UserContext` |
| `app/api/errors.py` | Domen xatolari → xavfsiz JSON (`{error, message}`) |
| `app/api/schemas.py` | So'rov tanalari validatsiyasi |
| `app/api/routes_catalog.py` | `GET /api/me`, `/api/layout`, `/api/shelves/{id}`, `/api/search`, `/api/items/{id}/thumb`, `POST /api/placements/{id}/stock` |
| `app/api/routes_ai.py` | `POST /api/recognitions`, `GET/edit/confirm/cancel /api/recognitions/{id}`, `POST /api/find-by-photo` |

### WebApp (frontend)
| Fayl | Vazifasi |
|---|---|
| `webapp/index.html` | Sahifa tuzilmasi (4 tab) |
| `webapp/css/styles.css` | "Aurora" glassmorphism dizayn, mobil-birinchi, qorong'i rejim |
| `webapp/js/app.js` | Kirish: Telegram, profil, tablar |
| `webapp/js/api.js` | API eshigi (initData header, xatolar) |
| `webapp/js/ui.js` | DOM yordamchilari (faqat `textContent` — XSS himoyasi), toast, loader |
| `webapp/js/cards.js` | Mahsulot kartochkasi (qidiruv va rasm natijalari uchun umumiy) |
| `webapp/js/search.js` | Qidiruv |
| `webapp/js/map.js` | Xarita va javon oynasi |
| `webapp/js/photo_find.js` | Rasm bo'yicha topish |
| `webapp/js/add.js` | Javonga qo'shish (xodim) |

### Bot ⇄ WebApp sinxronligi (10-qoida)
| Amal | Servis funksiyasi | Bot handler | WebApp API |
|---|---|---|---|
| Qidiruv | `search_service.search_items` | `search.on_text_search` | `GET /api/search` |
| Rasm bilan topish | `visual_match_service.find_by_photo` | `find_photo.on_find_photo` | `POST /api/find-by-photo` |
| Javon ko'rish | `shelf_service.shelf_contents` | `browse._show_level` | `GET /api/shelves/{id}` |
| Rasm → ro'yxat | `recognition_service.recognize_shelf_photo` | `add_items.on_shelf_photo` | `POST /api/recognitions` |
| Tahrir | `recognition_service.edit_batch` | `add_items.on_toggle / on_edit_text` | `POST .../edit` |
| Tasdiqlash | `recognition_service.confirm_batch` | `add_items.on_confirm` | `POST .../confirm` |
| Bekor qilish | `recognition_service.cancel_batch` | `add_items.on_cancel` | `POST .../cancel` |
| Qoldiq | `catalog_service.change_stock` | `search.on_stock` | `POST /api/placements/{id}/stock` |

### Testlar (`tests/`)
`test_text_normalize`, `test_auth`, `test_ai_parsing`, `test_layout_and_search`,
`test_recognition_and_stock`, `test_visual_and_misc`, `test_api`, `test_bot_flow` — 41 ta test.

---

## 🔐 Xavfsizlik va ishonchlilik
- Kalitlar faqat env'da (`.env` Git'ga kirmaydi). Gemini kaliti URL'da emas, header'da.
- WebApp: har so'rovda Telegram `initData` HMAC + muddat (24 soat) tekshiriladi.
- Rollar: mijoz faqat ko'radi; xodim qo'shadi/qoldiqni o'zgartiradi; egasi xodim tayinlaydi.
  Tasdiqlanmagan ro'yxatni faqat uni yaratgan foydalanuvchi ochadi/tasdiqlaydi.
- Tasdiqlash idempotent (atomik `pending → confirmed`), ikki marta bosish dublikat yaratmaydi.
- Rate limit: umumiy 40/daq, AI 6/daq har foydalanuvchiga; Gemini'ga parallel ≤3 so'rov, retry.
- AI ishonchi past (<60%) bo'lgan elementlar ⚠️ bilan, avtomatik o'chirilgan holda ko'rsatiladi.
- Rasm: format/hajm (≤10 MB)/"decompression bomb" tekshiruvi.
- AI kutilayotganda baza ulanishi band qilinmaydi (masshtab uchun).

## 🚀 Railway'ga joylash
1. Railway → New Project → GitHub repo → **+ PostgreSQL** qo'shing.
2. Service → **Variables** ga kiriting:
   - `BOT_TOKEN` — @BotFather tokeni
   - `ADMIN_TELEGRAM_IDS` — do'kon egasi ID si (bilish uchun botga `/myid`)
   - `GEMINI_API_KEY` — bepul: https://aistudio.google.com/apikey
   - `DATABASE_URL` — `${{Postgres.DATABASE_URL}}`
   - (ixtiyoriy) `WEBHOOK_SECRET` — tasodifiy uzun satr; berilsa webhook rejimi, aks holda polling
3. Settings → Networking → **Generate Domain** (`RAILWAY_PUBLIC_DOMAIN` avtomatik WebApp manzili bo'ladi).
4. Ishga tushish buyrug'i `railway.json` da: `alembic upgrade head && python -m app.main`.
5. @BotFather → `/setmenubutton` → WebApp URL (ixtiyoriy; bot menyusida tugma baribir bor).

## 💻 Lokal ishga tushirish
```bash
pip install -r requirements-dev.txt
cp .env.example .env        # kalitlarni kiriting
alembic upgrade head
python -m app.main
pytest                      # testlar
```

## 📈 Masshtab yo'l xaritasi (keyingi bosqichlar)
- Bir nechta instans: `MemoryStorage` → `RedisStorage`, `RateLimiter` → Redis (interfeys o'zgarmaydi).
- Juda katta katalog: vizual qidiruvga embedding + `pgvector`.
- Ko'p do'kon: sxema tayyor (`store_id` hamma joyda), UI'da do'kon tanlash qo'shiladi.
- Eski tasdiqlanmagan ro'yxatlarni tozalovchi davriy vazifa (TTL 24 soat allaqachon tekshiriladi).
