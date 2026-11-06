"""Markazlashtirilgan konstantalar (magic number'lar shu yerda)."""

# --- Do'kon tuzilmasi ---
DEFAULT_STORE_SLUG = "main"
DEFAULT_STORE_NAME = "Books Road"
MAX_SHELF_LEVELS = 12          # bitta javonda eng ko'p qator
LEVEL_NUMBERING_HINT = "1-qator — eng yuqori qator"

# --- Rollar ---
ROLE_OWNER = "owner"
ROLE_STAFF = "staff"
EDITOR_ROLES = frozenset({ROLE_OWNER, ROLE_STAFF})

# --- Mahsulot turlari (kengaytirish mumkin) ---
KIND_LABELS: dict[str, str] = {
    "book": "📚 Kitob",
    "perfume": "🌸 Attorlik",
    "prayer_mat": "🕌 Joynamoz",
    "stationery": "✏️ Kanselyariya",
    "souvenir": "🎁 Sovg'a",
    "other": "📦 Boshqa",
}
DEFAULT_KIND = "other"

# --- Joylashuv holati ---
STATUS_IN_STOCK = "in_stock"
STATUS_OUT = "out_of_stock"

# --- Validatsiya chegaralari ---
MAX_TITLE_LEN = 255
MAX_AUTHOR_LEN = 255
MAX_DESCRIPTION_LEN = 1000
MAX_QUERY_LEN = 120
MIN_QUERY_LEN = 2
MAX_QUANTITY = 9999
MAX_ITEMS_PER_PHOTO = 60
MAX_PHOTO_BYTES = 10 * 1024 * 1024
AI_IMAGE_MAX_SIDE = 1600       # AI ga yuborishdan oldin kichraytirish
THUMB_MAX_SIDE = 192           # bazada saqlanadigan kichik rasm
DOMINANT_COLORS = 3

# --- Qidiruv ---
SEARCH_CANDIDATE_LIMIT = 300
SEARCH_RESULT_LIMIT = 10
SEARCH_MIN_SCORE = 55

# --- Rasm bo'yicha topish ---
VISUAL_CANDIDATE_LIMIT = 200
VISUAL_TOP_FOR_RERANK = 8
VISUAL_CONFIDENT_SCORE = 0.75
VISUAL_MIN_SCORE = 0.30
VISUAL_TIE_MARGIN = 0.05       # 1- va 2-o'rin farqi shundan kichik bo'lsa — noaniq

# --- AI ---
AI_TIMEOUT_SECONDS = 60
AI_MAX_RETRIES = 2
AI_MAX_CONCURRENCY = 3
AI_LOW_CONFIDENCE = 0.6

# --- Rate limit (har bir foydalanuvchi uchun) ---
RATE_GENERAL_PER_MIN = 40
RATE_AI_PER_MIN = 6

# --- Tanib olish partiyasi ---
BATCH_PENDING = "pending"
BATCH_CONFIRMED = "confirmed"
BATCH_CANCELLED = "cancelled"
BATCH_TTL_HOURS = 24

# --- WebApp auth ---
INIT_DATA_MAX_AGE_SECONDS = 24 * 3600
