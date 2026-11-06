"""AI javobini tekshirish: noto'g'ri/yarim JSON bazaga tushmasin."""
import json
import logging

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.ai.base import AIError, DetectedItem, MatchChoice
from app.constants import (
    DEFAULT_KIND, KIND_LABELS, MAX_AUTHOR_LEN, MAX_DESCRIPTION_LEN, MAX_ITEMS_PER_PHOTO,
    MAX_QUANTITY, MAX_TITLE_LEN,
)
from app.services.text_normalize import clean_user_text

logger = logging.getLogger(__name__)
_BOX_MAX = 1000


class _RawItem(BaseModel):
    title: str = ""
    author: str = ""
    kind: str = DEFAULT_KIND
    colors: list[str] = Field(default_factory=list)
    shape: str = ""
    visual_description: str = ""
    quantity: int = 1
    confidence: float = 0.0
    box_2d: list[int] | None = None

    @field_validator("kind")
    @classmethod
    def _kind(cls, value: str) -> str:
        return value if value in KIND_LABELS else DEFAULT_KIND

    @field_validator("confidence")
    @classmethod
    def _confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @field_validator("quantity")
    @classmethod
    def _quantity(cls, value: int) -> int:
        return max(1, min(MAX_QUANTITY, int(value)))


def _valid_box(box: list[int] | None) -> list[int] | None:
    if not box or len(box) != 4:
        return None
    ymin, xmin, ymax, xmax = (max(0, min(_BOX_MAX, int(v))) for v in box)
    if ymax <= ymin or xmax <= xmin:
        return None
    return [ymin, xmin, ymax, xmax]


def _to_detected(raw: _RawItem) -> DetectedItem | None:
    title = clean_user_text(raw.title, MAX_TITLE_LEN)
    if not title:
        return None
    return DetectedItem(
        title=title,
        author=clean_user_text(raw.author, MAX_AUTHOR_LEN),
        kind=raw.kind,
        colors=[c for c in (clean_user_text(x, 40) for x in raw.colors[:5]) if c],
        shape=clean_user_text(raw.shape, 64),
        visual_description=clean_user_text(raw.visual_description, MAX_DESCRIPTION_LEN),
        quantity=raw.quantity,
        confidence=raw.confidence,
        box=_valid_box(raw.box_2d),
    )


def load_json(text: str) -> dict:
    """Model ba'zan ```json ... ``` bilan o'raydi — tozalab o'qiymiz."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned[4:] if cleaned.lower().startswith("json") else cleaned
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIError("AI JSON emas javob qaytardi") from exc
    if not isinstance(data, dict):
        raise AIError("AI javobi obyekt emas")
    return data


def parse_detected_items(text: str) -> list[DetectedItem]:
    data = load_json(text)
    raw_items = data.get("items")
    if not isinstance(raw_items, list):
        raise AIError("AI javobida items ro'yxati yo'q")
    items: list[DetectedItem] = []
    for raw in raw_items[:MAX_ITEMS_PER_PHOTO]:
        try:
            detected = _to_detected(_RawItem.model_validate(raw))
        except (ValidationError, TypeError, ValueError) as exc:
            logger.warning("AI elementi o'tkazib yuborildi: %s", exc.__class__.__name__)
            continue
        if detected:
            items.append(detected)
    return items


def parse_description(text: str) -> DetectedItem | None:
    data = load_json(text)
    if not data.get("found"):
        return None
    try:
        return _to_detected(_RawItem.model_validate(data))
    except ValidationError as exc:
        raise AIError("AI tavsifi noto'g'ri formatda") from exc


def parse_match(text: str, candidates_count: int) -> MatchChoice:
    data = load_json(text)
    try:
        index = int(data.get("index", -1))
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.0))))
    except (TypeError, ValueError) as exc:
        raise AIError("AI tanlovi noto'g'ri formatda") from exc
    if index < 0 or index >= candidates_count:
        return MatchChoice(index=None, confidence=confidence)
    return MatchChoice(index=index, confidence=confidence)
