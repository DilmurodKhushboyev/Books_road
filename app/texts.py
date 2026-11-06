"""Foydalanuvchiga ko'rinadigan xato xabarlari — bot va WebApp uchun yagona manba.

Ichki tuzilma (fayl yo'li, stack trace, sxema) hech qachon foydalanuvchiga chiqmaydi.
"""

ERRORS: dict[str, str] = {
    "too_short": "So'rov juda qisqa. Kamida 2 ta harf yozing.",
    "too_long": "So'rov juda uzun. Qisqaroq yozing.",
    "forbidden": "Bu amal faqat do'kon xodimlari uchun.",
    "owner_only": "Bu amal faqat do'kon egasi uchun.",
    "rate_limited": "Juda tez-tez so'rov yuboryapsiz. Bir daqiqadan so'ng urinib ko'ring.",
    "ai_unavailable": "AI hozircha mavjud emas (ulanmagan yoki limit tugagan). Keyinroq urinib ko'ring.",
    "ai_error": "AI rasmni tahlil qila olmadi. Boshqa, tiniqroq rasm yuboring.",
    "invalid_image": "Rasmni o'qib bo'lmadi. JPG/PNG formatda, 10 MB dan kichik rasm yuboring.",
    "shelf_not_found": "Javon topilmadi.",
    "bad_level": "Bunday qator yo'q.",
    "batch_not_found": "Ro'yxat topilmadi.",
    "batch_closed": "Bu ro'yxat allaqachon tasdiqlangan yoki bekor qilingan.",
    "batch_expired": "Ro'yxat muddati o'tgan. Rasmni qayta yuboring.",
    "not_found": "Topilmadi.",
    "bad_action": "Noto'g'ri amal.",
    "empty_title": "Nom bo'sh bo'lishi mumkin emas.",
    "unauthorized": "Telegram orqali kiring (WebApp ma'lumotlari tasdiqlanmadi).",
    "internal": "Kutilmagan xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.",
}


def error_text(code: str) -> str:
    return ERRORS.get(code, ERRORS["internal"])
