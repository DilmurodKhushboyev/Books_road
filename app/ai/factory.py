"""AI provayderini tanlash. Kalit bo'lmasa — DisabledAI (aniq xato beradi)."""
import logging

from app.ai.base import AIProvider, AIUnavailable, DetectedItem, MatchChoice
from app.config import Settings

logger = logging.getLogger(__name__)


class DisabledAI:
    async def detect_items(self, image: bytes) -> list[DetectedItem]:
        raise AIUnavailable("AI ulanmagan")

    async def describe_item(self, image: bytes) -> DetectedItem | None:
        raise AIUnavailable("AI ulanmagan")

    async def choose_match(self, image: bytes, candidates: list[dict]) -> MatchChoice:
        raise AIUnavailable("AI ulanmagan")

    async def close(self) -> None:
        return None


def build_ai_provider(settings: Settings) -> AIProvider:
    if not settings.ai_enabled:
        logger.warning("GEMINI_API_KEY berilmagan — AI funksiyalari o'chiq")
        return DisabledAI()
    from app.ai.gemini import GeminiProvider

    return GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.gemini_base_url)
