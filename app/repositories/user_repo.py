"""Foydalanuvchi va do'kon a'zoligi bo'yicha baza so'rovlari."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import StoreMember, User


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def upsert_user(
    session: AsyncSession, telegram_id: int, full_name: str, username: str | None
) -> User:
    user = await get_by_telegram_id(session, telegram_id)
    if user is None:
        user = User(telegram_id=telegram_id, full_name=full_name, username=username)
        session.add(user)
        await session.flush()
        return user
    if user.full_name != full_name or user.username != username:
        user.full_name, user.username = full_name, username
    return user


async def get_role(session: AsyncSession, store_id: int, user_id: int) -> str | None:
    result = await session.execute(
        select(StoreMember.role).where(
            StoreMember.store_id == store_id, StoreMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def set_role(session: AsyncSession, store_id: int, user_id: int, role: str) -> None:
    result = await session.execute(
        select(StoreMember).where(StoreMember.store_id == store_id, StoreMember.user_id == user_id)
    )
    member = result.scalar_one_or_none()
    if member is None:
        session.add(StoreMember(store_id=store_id, user_id=user_id, role=role))
    else:
        member.role = role
    await session.flush()
