"""AI "eshigi": boshqa modullar faqat shu interfeys orqali AI bilan gaplashadi.

Provayderni almashtirish (Gemini -> boshqa) faqat factory.py ni o'zgartiradi.
"""
from dataclasses import dataclass, field
from typing import Protocol


class AIError(Exception):
    """AI javob bermadi yoki noto'g'ri javob qaytardi."""


class AIUnavailable(AIError):
    """AI ulanmagan (kalit yo'q) yoki limit tugagan."""


@dataclass
class DetectedItem:
    title: str
    author: str = ""
    kind: str = "other"
    colors: list[str] = field(default_factory=list)
    shape: str = ""
    visual_description: str = ""
    quantity: int = 1
    confidence: float = 0.0
    # Normallashtirilgan [ymin, xmin, ymax, xmax] (0..1000) yoki None
    box: list[int] | None = None


@dataclass
class MatchChoice:
    index: int | None          # nomzodlar ro'yxatidagi indeks yoki None (hech biri emas)
    confidence: float


class AIProvider(Protocol):
    async def detect_items(self, image: bytes) -> list[DetectedItem]:
        """Javon rasmidagi barcha narsalarni (nom, rang, shakl...) aniqlaydi."""
        ...

    async def describe_item(self, image: bytes) -> DetectedItem | None:
        """Bitta narsa rasmini tavsiflaydi (rasm bo'yicha qidirish uchun)."""
        ...

    async def choose_match(self, image: bytes, candidates: list[dict]) -> MatchChoice:
        """Rasmdagi narsa nomzodlardan qaysi biri ekanini tanlaydi."""
        ...
