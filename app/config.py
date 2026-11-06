"""Muhit o'zgaruvchilaridan sozlamalarni o'qish (yagona eshik).

Hech qanday kalit/token kodga yozilmaydi — faqat env (Railway Variables / .env).
"""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(default="", description="Telegram bot token")
    admin_telegram_ids: str = Field(default="", description="Vergul bilan ajratilgan ID lar")

    database_url: str = "sqlite+aiosqlite:///./books_road.db"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    port: int = 8000
    webapp_url: str = ""
    railway_public_domain: str = ""
    webhook_secret: str = ""
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def _async_driver(cls, value: str) -> str:
        """Railway `postgresql://` beradi — async drayverga o'giramiz."""
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://"):]
        if value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://"):]
        return value

    @property
    def admin_ids(self) -> frozenset[int]:
        ids: set[int] = set()
        for part in self.admin_telegram_ids.split(","):
            part = part.strip()
            if part.isdigit():
                ids.add(int(part))
        return frozenset(ids)

    @property
    def public_url(self) -> str:
        if self.webapp_url:
            return self.webapp_url.rstrip("/")
        if self.railway_public_domain:
            return f"https://{self.railway_public_domain}"
        return ""

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def use_webhook(self) -> bool:
        return bool(self.webhook_secret and self.public_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
