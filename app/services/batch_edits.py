"""Tasdiqlanmagan partiyadagi elementlarni tahrirlash va ko'rinishi (sof funksiyalar)."""
from dataclasses import dataclass

from app.constants import AI_LOW_CONFIDENCE, KIND_LABELS, MAX_QUANTITY, MAX_TITLE_LEN
from app.db.models import RecognitionBatch
from app.services.text_normalize import clean_user_text, normalize_text


@dataclass
class BatchEdit:
    index: int
    include: bool | None = None
    title: str | None = None
    author: str | None = None
    kind: str | None = None
    quantity: int | None = None


def apply_edits(items: list[dict], edits: list[BatchEdit]) -> list[dict]:
    """Yangi ro'yxat qaytaradi (JSON ustun o'zgarishi SQLAlchemy'ga ko'rinsin)."""
    result = [dict(item) for item in items]
    for edit in edits:
        if not 0 <= edit.index < len(result):
            continue
        item = result[edit.index]
        if edit.include is not None:
            item["include"] = bool(edit.include)
        if edit.title is not None:
            title = clean_user_text(edit.title, MAX_TITLE_LEN)
            if normalize_text(title):
                item["title"] = title
                item["confidence"] = 1.0          # inson tasdiqladi
        if edit.author is not None:
            item["author"] = clean_user_text(edit.author, MAX_TITLE_LEN)
        if edit.kind is not None and edit.kind in KIND_LABELS:
            item["kind"] = edit.kind
        if edit.quantity is not None:
            item["quantity"] = max(1, min(MAX_QUANTITY, int(edit.quantity)))
    return result


def batch_view(batch: RecognitionBatch) -> dict:
    items = []
    for index, item in enumerate(batch.items or []):
        items.append({
            "index": index,
            "title": item.get("title", ""),
            "author": item.get("author", ""),
            "kind": item.get("kind", "other"),
            "kind_label": KIND_LABELS.get(item.get("kind", "other"), "📦"),
            "colors": item.get("colors", []),
            "quantity": item.get("quantity", 1),
            "confidence": item.get("confidence", 0.0),
            "low_confidence": item.get("confidence", 0.0) < AI_LOW_CONFIDENCE,
            "include": bool(item.get("include")),
            "thumb": f"data:image/jpeg;base64,{item['thumb_b64']}" if item.get("thumb_b64") else "",
        })
    return {
        "batch_id": batch.id, "shelf_id": batch.shelf_id, "level": batch.level,
        "status": batch.status, "avg_confidence": batch.avg_confidence, "items": items,
    }
