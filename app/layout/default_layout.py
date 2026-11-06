"""Do'kon andozasi (PDF obmer rejasi asosida, 77.9 m²).

O'rtadagi bo'shliqda 2 ta uzun javon qatori (bo'lim) bor:
  - har bo'limda 10 ta javon: uzunasiga 5 ta "old tomon" + orqasiga 5 ta "orqa tomon"
  - jami 20 ta javon, har birida 8 ta qator (bo'yiga)

Boshqa do'kon uchun shu tuzilmadagi yangi dict yozish kifoya (kod o'zgarmaydi).
"""
from dataclasses import dataclass

SIDE_FRONT = "front"
SIDE_BACK = "back"
SIDE_LABELS = {SIDE_FRONT: "old tomon", SIDE_BACK: "orqa tomon"}

DEFAULT_LEVELS = 8
SHELVES_PER_SIDE = 5


@dataclass(frozen=True)
class ShelfSpec:
    code: str
    side: str
    position: int
    levels_count: int = DEFAULT_LEVELS


@dataclass(frozen=True)
class SectionSpec:
    code: str
    name: str
    position: int
    shelves: tuple[ShelfSpec, ...]


def _build_section(code: str, name: str, position: int) -> SectionSpec:
    shelves: list[ShelfSpec] = []
    for idx in range(SHELVES_PER_SIDE * 2):
        side = SIDE_FRONT if idx < SHELVES_PER_SIDE else SIDE_BACK
        shelves.append(ShelfSpec(code=f"{code}{idx + 1}", side=side, position=idx + 1))
    return SectionSpec(code=code, name=name, position=position, shelves=tuple(shelves))


DEFAULT_LAYOUT: tuple[SectionSpec, ...] = (
    _build_section("A", "A bo'lim (chap qator)", 1),
    _build_section("B", "B bo'lim (o'ng qator)", 2),
)
