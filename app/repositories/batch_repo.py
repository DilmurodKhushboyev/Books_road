"""Tanib olish partiyalari (tasdiqlanmagan AI natijalari) bo'yicha so'rovlar."""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import BATCH_PENDING
from app.db.models import RecognitionBatch


async def create_batch(session: AsyncSession, batch: RecognitionBatch) -> RecognitionBatch:
    session.add(batch)
    await session.flush()
    return batch


async def get_user_batch(
    session: AsyncSession, batch_id: int, user_id: int, for_update: bool = False
) -> RecognitionBatch | None:
    """Faqat egasining partiyasi qaytadi (boshqa user_id bilan ochib bo'lmaydi)."""
    query = select(RecognitionBatch).where(
        RecognitionBatch.id == batch_id, RecognitionBatch.user_id == user_id
    )
    if for_update:
        query = query.with_for_update()
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def claim_batch(session: AsyncSession, batch_id: int, new_status: str) -> bool:
    """pending -> new_status atomik o'tishi. Ikki marta bosilsa ikkinchisi False oladi."""
    result = await session.execute(
        update(RecognitionBatch)
        .where(RecognitionBatch.id == batch_id, RecognitionBatch.status == BATCH_PENDING)
        .values(status=new_status)
    )
    return result.rowcount == 1
