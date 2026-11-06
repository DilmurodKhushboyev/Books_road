"""AI uchun ko'rsatmalar (prompt) va javob sxemalari."""
from app.constants import KIND_LABELS, MAX_ITEMS_PER_PHOTO

_KINDS = ", ".join(KIND_LABELS.keys())

_ITEM_PROPERTIES = {
    "title": {"type": "STRING"},
    "author": {"type": "STRING"},
    "kind": {"type": "STRING", "enum": list(KIND_LABELS.keys())},
    "colors": {"type": "ARRAY", "items": {"type": "STRING"}},
    "shape": {"type": "STRING"},
    "visual_description": {"type": "STRING"},
    "quantity": {"type": "INTEGER"},
    "confidence": {"type": "NUMBER"},
    "box_2d": {"type": "ARRAY", "items": {"type": "INTEGER"}},
}

DETECT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "items": {
            "type": "ARRAY",
            "items": {"type": "OBJECT", "properties": _ITEM_PROPERTIES, "required": ["title", "kind", "confidence"]},
        }
    },
    "required": ["items"],
}

DESCRIBE_SCHEMA = {
    "type": "OBJECT",
    "properties": {"found": {"type": "BOOLEAN"}, **_ITEM_PROPERTIES},
    "required": ["found"],
}

MATCH_SCHEMA = {
    "type": "OBJECT",
    "properties": {"index": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}},
    "required": ["index", "confidence"],
}

_FIELD_RULES = f"""
Har bir narsa uchun:
- title: muqova/koreshokdagi nom AYNAN yozilganidek (lotin yoki kirill). Kitob bo'lmasa — qisqa nom
  (masalan "Yashil baxmal joynamoz", "Oud atiri 50ml").
- author: muallif yoki brend (bo'lmasa "").
- kind: quyidagilardan biri: {_KINDS}.
- colors: asosiy ranglar, o'zbekcha, 1-3 ta (masalan ["to'q ko'k", "oltin"]).
- shape: shakli (masalan "qalin kitob", "yupqa kitob", "flakon", "o'ralgan gilam", "quti").
- visual_description: muqovadagi rasm, naqsh, shrift, belgilar — 1-2 gap, o'zbekcha.
- quantity: shu narsadan nechta nusxa ko'rinmoqda.
- confidence: 0..1 — nomni qanchalik aniq o'qiganingiz. Taxmin qilsangiz past qo'ying, TO'QIMANG.
- box_2d: [ymin, xmin, ymax, xmax] 0..1000 oralig'ida.
"""

DETECT_PROMPT = f"""Siz kitob do'koni yordamchisisiz. Rasmda do'kon javonining bir qatori.
Ko'ringan barcha narsalarni (kitoblar, atirlar, joynamozlar va boshqalar) aniqlang.
Ko'pi bilan {MAX_ITEMS_PER_PHOTO} ta. Nomi o'qilmaydigan narsani ham kiriting, lekin confidence past bo'lsin.
{_FIELD_RULES}
Faqat JSON qaytaring."""

DESCRIBE_PROMPT = f"""Rasmda do'kondagi bitta narsa (kitob, atir, joynamoz yoki boshqa).
Uni do'kon bazasidan topish uchun tavsiflang. Narsa aniq ko'rinmasa found=false.
{_FIELD_RULES}
Faqat JSON qaytaring."""


def build_match_prompt(candidates: list[dict]) -> str:
    lines = []
    for idx, cand in enumerate(candidates):
        lines.append(
            f"{idx}. {cand.get('title', '')} | {cand.get('author', '')} | ranglar: "
            f"{', '.join(cand.get('colors') or [])} | {cand.get('visual_description', '')}"
        )
    listing = "\n".join(lines)
    return f"""Rasmdagi narsa quyidagi bazadagi nomzodlardan qaysi biri?
{listing}
Mos kelsa uning raqamini (index), hech biri mos kelmasa index=-1 qaytaring.
confidence: 0..1. Ishonchingiz past bo'lsa — past qo'ying. Faqat JSON."""
