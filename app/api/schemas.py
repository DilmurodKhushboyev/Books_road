"""API so'rov tanalari — server tomonida validatsiya (klientga ishonilmaydi)."""
from typing import Literal

from pydantic import BaseModel, Field

from app.constants import MAX_AUTHOR_LEN, MAX_ITEMS_PER_PHOTO, MAX_QUANTITY, MAX_TITLE_LEN
from app.services.batch_edits import BatchEdit


class BatchEditIn(BaseModel):
    index: int = Field(ge=0, lt=MAX_ITEMS_PER_PHOTO)
    include: bool | None = None
    title: str | None = Field(default=None, max_length=MAX_TITLE_LEN)
    author: str | None = Field(default=None, max_length=MAX_AUTHOR_LEN)
    kind: str | None = Field(default=None, max_length=32)
    quantity: int | None = Field(default=None, ge=1, le=MAX_QUANTITY)

    def to_domain(self) -> BatchEdit:
        return BatchEdit(**self.model_dump())


class BatchEditsIn(BaseModel):
    edits: list[BatchEditIn] = Field(default_factory=list, max_length=MAX_ITEMS_PER_PHOTO)

    def to_domain(self) -> list[BatchEdit]:
        return [edit.to_domain() for edit in self.edits]


class StockIn(BaseModel):
    action: Literal["inc", "dec", "out", "in"]
