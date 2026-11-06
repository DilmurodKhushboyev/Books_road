"""Foydalanuvchi konteksti va huquqlar — bot ham, WebApp ham shu yerdan foydalanadi."""
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import DEFAULT_STORE_SLUG, EDITOR_ROLES, ROLE_OWNER, ROLE_STAFF
from app.repositories import layout_repo, user_repo
from app.services.text_normalize import clean_user_text

_NAME_MAX = 255


class AccessDenied(PermissionError):
    """Foydalanuvchida bu amal uchun huquq yo'q."""


@dataclass(frozen=True)
class UserContext:
    user_id: int
    telegram_id: int
    store_id: int
    role: str | None
    is_blocked: bool = False

    @property
    def can_edit(self) -> bool:
        return self.role in EDITOR_ROLES and not self.is_blocked

    @property
    def is_owner(self) -> bool:
        return self.role == ROLE_OWNER and not self.is_blocked


async def resolve_context(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: str | None,
    admin_ids: frozenset[int],
) -> UserContext:
    """Foydalanuvchini ro'yxatdan o'tkazadi/yangilaydi va do'kondagi rolini aniqlaydi."""
    store = await layout_repo.get_store_by_slug(session, DEFAULT_STORE_SLUG)
    if store is None:
        raise RuntimeError("Do'kon hali yaratilmagan")
    user = await user_repo.upsert_user(
        session, telegram_id, clean_user_text(full_name, _NAME_MAX), username
    )
    role = await user_repo.get_role(session, store.id, user.id)
    if telegram_id in admin_ids and role != ROLE_OWNER:
        await user_repo.set_role(session, store.id, user.id, ROLE_OWNER)
        role = ROLE_OWNER
    return UserContext(user.id, telegram_id, store.id, role, user.is_blocked)


def require_editor(ctx: UserContext) -> None:
    if not ctx.can_edit:
        raise AccessDenied("Faqat do'kon xodimlari uchun")


async def grant_staff(session: AsyncSession, ctx: UserContext, target_telegram_id: int) -> bool:
    """Egasi boshqa foydalanuvchini xodim qiladi. Foydalanuvchi botga /start bosgan bo'lishi kerak."""
    if not ctx.is_owner:
        raise AccessDenied("Faqat do'kon egasi uchun")
    target = await user_repo.get_by_telegram_id(session, target_telegram_id)
    if target is None:
        return False
    current = await user_repo.get_role(session, ctx.store_id, target.id)
    if current != ROLE_OWNER:
        await user_repo.set_role(session, ctx.store_id, target.id, ROLE_STAFF)
    return True
