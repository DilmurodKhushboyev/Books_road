"""Servis natijalarini Telegram HTML matniga aylantirish (barcha matn escape qilinadi)."""
from html import escape

from app.bot import texts

_TG_LIMIT = 3900
_TITLE_SHORT = 60


def _short(text: str, limit: int = _TITLE_SHORT) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _cut(text: str) -> str:
    return text if len(text) <= _TG_LIMIT else text[:_TG_LIMIT] + "\n…"


def item_block(view: dict) -> str:
    author = f" — <i>{escape(view['author'])}</i>" if view["author"] else ""
    lines = [f"{view['kind_label'].split(' ')[0]} <b>{escape(view['title'])}</b>{author}"]
    if not view["placements"]:
        lines.append(f"   {texts.NO_PLACEMENT}")
    for place in view["placements"]:
        status = (texts.IN_STOCK.format(qty=place["quantity"]) if place["in_stock"]
                  else texts.OUT_OF_STOCK)
        lines.append(f"   📍 {escape(place['location'])}\n   {status}")
    return "\n".join(lines)


def search_results(query: str, views: list[dict]) -> str:
    if not views:
        return texts.NOT_FOUND.format(query=escape(query))
    blocks = [texts.RESULTS_HEADER.format(query=escape(query))]
    blocks += [f"{i}. {item_block(view)}" for i, view in enumerate(views, start=1)]
    return _cut("\n\n".join(blocks))


def batch_review(batch: dict, location: str) -> str:
    items = batch["items"]
    header = texts.REVIEW_HEADER.format(
        location=escape(location), count=len(items), avg=round(batch["avg_confidence"] * 100)
    )
    lines = []
    for item in items:
        mark = "✅" if item["include"] else "▫️"
        warn = f" ⚠️{round(item['confidence'] * 100)}%" if item["low_confidence"] else ""
        author = f" — {escape(_short(item['author'], 30))}" if item["author"] else ""
        qty = f" ×{item['quantity']}" if item["quantity"] > 1 else ""
        lines.append(f"{item['index'] + 1}. {mark} {escape(_short(item['title']))}{author}{qty}{warn}")
    return _cut(header + "\n" + "\n".join(lines))


def photo_find_result(result: dict) -> str:
    if not result["recognized"]:
        return texts.PHOTO_NOT_RECOGNIZED
    query = result["query"]
    author = f" — {escape(query['author'])}" if query["author"] else ""
    parts = [texts.PHOTO_RECOGNIZED_AS.format(
        title=escape(query["title"]), author=author, conf=round(query["confidence"] * 100)
    )]
    if not result["results"]:
        parts.append(texts.PHOTO_NO_MATCH)
        return "\n\n".join(parts)
    if not result["confident"]:
        parts.append(texts.PHOTO_UNSURE)
    for i, view in enumerate(result["results"], start=1):
        parts.append(f"{i}. {item_block(view)}  <i>({round(view['score'] * 100)}%)</i>")
    return _cut("\n\n".join(parts))


def shelf_level(contents: dict) -> str:
    level = contents["levels"][0]
    title = (f"🗄 <b>{escape(contents['code'])}</b> javon ({escape(contents['side_label'])}) → "
             f"<b>{level['level']}-qator</b>")
    if not level["items"]:
        return f"{title}\n\n{texts.SHELF_EMPTY}"
    lines = [title, ""]
    for i, item in enumerate(level["items"], start=1):
        status = f"✅ {item['quantity']}" if item["in_stock"] else "❌ qolmagan"
        author = f" — <i>{escape(_short(item['author'], 30))}</i>" if item["author"] else ""
        lines.append(f"{i}. {escape(_short(item['title']))}{author} · {status}")
    return _cut("\n".join(lines))
