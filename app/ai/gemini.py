"""Google Gemini (bepul tarif) — AIProvider implementatsiyasi, REST orqali.

Kalit faqat env'dan (GEMINI_API_KEY) va URL'da emas, header'da yuboriladi.
"""
import asyncio
import base64
import logging

import httpx

from app.ai import parsing, prompts
from app.ai.base import AIError, AIUnavailable, DetectedItem, MatchChoice
from app.constants import AI_MAX_CONCURRENCY, AI_MAX_RETRIES, AI_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_BACKOFF_BASE_SECONDS = 2


class GeminiProvider:
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
        self._semaphore = asyncio.Semaphore(AI_MAX_CONCURRENCY)
        self._client = httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS)

    async def close(self) -> None:
        await self._client.aclose()

    async def detect_items(self, image: bytes) -> list[DetectedItem]:
        text = await self._generate(prompts.DETECT_PROMPT, image, prompts.DETECT_SCHEMA)
        return parsing.parse_detected_items(text)

    async def describe_item(self, image: bytes) -> DetectedItem | None:
        text = await self._generate(prompts.DESCRIBE_PROMPT, image, prompts.DESCRIBE_SCHEMA)
        return parsing.parse_description(text)

    async def choose_match(self, image: bytes, candidates: list[dict]) -> MatchChoice:
        if not candidates:
            return MatchChoice(index=None, confidence=0.0)
        prompt = prompts.build_match_prompt(candidates)
        text = await self._generate(prompt, image, prompts.MATCH_SCHEMA)
        return parsing.parse_match(text, len(candidates))

    async def _generate(self, prompt: str, image: bytes, schema: dict) -> str:
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(image).decode()}},
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "temperature": 0.1,
            },
        }
        async with self._semaphore:
            data = await self._post_with_retry(payload)
        return self._extract_text(data)

    async def _post_with_retry(self, payload: dict) -> dict:
        headers = {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}
        for attempt in range(AI_MAX_RETRIES + 1):
            try:
                response = await self._client.post(self._url, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                logger.warning("Gemini tarmoq xatosi (urinish %s): %s", attempt + 1, exc.__class__.__name__)
                if attempt >= AI_MAX_RETRIES:
                    raise AIError("AI xizmatiga ulanib bo'lmadi") from exc
            else:
                if response.status_code == 200:
                    return response.json()
                logger.warning("Gemini status=%s (urinish %s)", response.status_code, attempt + 1)
                if response.status_code not in _RETRY_STATUSES or attempt >= AI_MAX_RETRIES:
                    if response.status_code == 429:
                        raise AIUnavailable("AI limiti tugadi")
                    raise AIError(f"AI xatosi: status {response.status_code}")
            await asyncio.sleep(_BACKOFF_BASE_SECONDS * (2 ** attempt))
        raise AIError("AI javob bermadi")

    @staticmethod
    def _extract_text(data: dict) -> str:
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts)
        except (KeyError, IndexError, TypeError) as exc:
            reason = (data.get("promptFeedback") or {}).get("blockReason", "noma'lum")
            raise AIError(f"AI bo'sh javob qaytardi ({reason})") from exc
