"""Rasm bilan ishlash: tekshirish, AI uchun tayyorlash, kesish, rang olish.

Barcha funksiyalar sinxron (CPU) — chaqiruvchi asyncio.to_thread() orqali chaqiradi.
"""
import io
import math

from PIL import Image, ImageOps, UnidentifiedImageError

from app.constants import AI_IMAGE_MAX_SIDE, DOMINANT_COLORS, MAX_PHOTO_BYTES, THUMB_MAX_SIDE

Image.MAX_IMAGE_PIXELS = 60_000_000      # "decompression bomb" himoyasi
_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "MPO"}
_BOX_SCALE = 1000
_JPEG_QUALITY_AI = 85
_JPEG_QUALITY_THUMB = 75
_COLOR_SAMPLE_SIDE = 64
_MAX_RGB_DISTANCE = math.sqrt(3 * 255 ** 2)


class InvalidImage(ValueError):
    """Fayl rasm emas, juda katta yoki buzilgan."""


def load_image(data: bytes) -> Image.Image:
    if not data:
        raise InvalidImage("Bo'sh fayl")
    if len(data) > MAX_PHOTO_BYTES:
        raise InvalidImage("Rasm juda katta")
    try:
        image = Image.open(io.BytesIO(data))
        if image.format not in _ALLOWED_FORMATS:
            raise InvalidImage("Qo'llab-quvvatlanmaydigan format")
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InvalidImage("Rasmni o'qib bo'lmadi") from exc
    return ImageOps.exif_transpose(image).convert("RGB")


def _to_jpeg(image: Image.Image, quality: int) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def prepare_for_ai(image: Image.Image) -> bytes:
    copy = image.copy()
    copy.thumbnail((AI_IMAGE_MAX_SIDE, AI_IMAGE_MAX_SIDE))
    return _to_jpeg(copy, _JPEG_QUALITY_AI)


def crop_box(image: Image.Image, box: list[int] | None) -> Image.Image:
    """AI box_2d [ymin, xmin, ymax, xmax] (0..1000) bo'yicha kesish; box yo'q — butun rasm."""
    if not box:
        return image
    width, height = image.size
    ymin, xmin, ymax, xmax = box
    area = (
        int(xmin * width / _BOX_SCALE), int(ymin * height / _BOX_SCALE),
        int(xmax * width / _BOX_SCALE), int(ymax * height / _BOX_SCALE),
    )
    if area[2] - area[0] < 2 or area[3] - area[1] < 2:
        return image
    return image.crop(area)


def make_thumbnail(image: Image.Image) -> bytes:
    copy = image.copy()
    copy.thumbnail((THUMB_MAX_SIDE, THUMB_MAX_SIDE))
    return _to_jpeg(copy, _JPEG_QUALITY_THUMB)


def dominant_colors(image: Image.Image, count: int = DOMINANT_COLORS) -> list[str]:
    """Eng ko'p uchraydigan ranglar (#rrggbb), ko'pdan kamga."""
    small = image.copy()
    small.thumbnail((_COLOR_SAMPLE_SIDE, _COLOR_SAMPLE_SIDE))
    quantized = small.quantize(colors=count + 2)
    palette = quantized.getpalette() or []
    counts = sorted(quantized.getcolors() or [], reverse=True)
    result: list[str] = []
    for _, index in counts[:count]:
        r, g, b = palette[index * 3: index * 3 + 3]
        result.append(f"#{r:02x}{g:02x}{b:02x}")
    return result


def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    value = value.lstrip("#")
    if len(value) != 6:
        return None
    try:
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
    except ValueError:
        return None


def color_similarity(first: list[str], second: list[str]) -> float:
    """0..1: har bir rang uchun eng yaqin juftlik bo'yicha o'rtacha o'xshashlik."""
    a = [c for c in (_hex_to_rgb(x) for x in first) if c]
    b = [c for c in (_hex_to_rgb(x) for x in second) if c]
    if not a or not b:
        return 0.0
    total = 0.0
    for color in a:
        nearest = min(math.dist(color, other) for other in b)
        total += 1.0 - nearest / _MAX_RGB_DISTANCE
    return total / len(a)
