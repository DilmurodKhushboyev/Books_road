"""Matnni qidiruv uchun normallashtirish.

- Kirill -> Lotin (o'zbek va rus): "Ўтган кунлар" == "O'tgan kunlar"
- Barcha apostrof variantlari (' ʻ ʼ ` ‘ ’ ´) olib tashlanadi: "o'tgan" == "otgan"
- Kichik harf, faqat harf/raqam/bo'shliq.
"""
import re
import unicodedata

_CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
    "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o", "қ": "q",
    "ғ": "g", "ҳ": "h",
}
_APOSTROPHES = "'ʻʼ`‘’´ʹ′"
_APOSTROPHE_RE = re.compile(f"[{re.escape(_APOSTROPHES)}]")
_NON_WORD_RE = re.compile(r"[^0-9a-z\s]+")
_SPACES_RE = re.compile(r"\s+")


def transliterate(text: str) -> str:
    return "".join(_CYR_TO_LAT.get(ch, ch) for ch in text)


def normalize_text(text: str | None) -> str:
    """Qidiruv/taqqoslash uchun kanonik shakl. None/bo'sh -> ''."""
    if not text:
        return ""
    value = unicodedata.normalize("NFKC", text).lower()
    value = transliterate(value)
    value = _APOSTROPHE_RE.sub("", value)
    # Lotin diakritikalarini soddalashtiramiz (é -> e)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = _NON_WORD_RE.sub(" ", value)
    return _SPACES_RE.sub(" ", value).strip()


def search_tokens(text: str, max_tokens: int = 3) -> list[str]:
    """Eng uzun (eng ma'noli) tokenlar — SQL nomzod tanlash uchun."""
    tokens = [t for t in normalize_text(text).split(" ") if len(t) >= 2]
    unique = list(dict.fromkeys(tokens))
    unique.sort(key=len, reverse=True)
    return unique[:max_tokens]


def clean_user_text(text: str | None, max_len: int) -> str:
    """Foydalanuvchi/AI matnini saqlashdan oldin tozalash (boshqaruv belgilarisiz)."""
    if not text:
        return ""
    value = "".join(ch for ch in str(text) if ch.isprintable())
    return _SPACES_RE.sub(" ", value).strip()[:max_len]
