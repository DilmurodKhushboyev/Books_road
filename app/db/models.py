"""ORM modellari. Tuzilma: Store -> Section(bo'lim) -> Shelf(javon) -> level(qator).

Item — katalogdagi narsa (kitob, attorlik, joynamoz...).
Placement — Item qaysi javonning qaysi qatorida, nechta, bor/qolmagan.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer,
    LargeBinary, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Store(Base):
    __tablename__ = "stores"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StoreMember(Base):
    __tablename__ = "store_members"
    __table_args__ = (UniqueConstraint("store_id", "user_id", name="uq_member_store_user"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Section(Base):
    __tablename__ = "sections"
    __table_args__ = (UniqueConstraint("store_id", "code", name="uq_section_store_code"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(128))
    position: Mapped[int] = mapped_column(Integer, default=0)
    shelves: Mapped[list["Shelf"]] = relationship(
        back_populates="section", order_by="Shelf.position", lazy="selectin"
    )


class Shelf(Base):
    __tablename__ = "shelves"
    __table_args__ = (UniqueConstraint("section_id", "code", name="uq_shelf_section_code"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(16))
    side: Mapped[str] = mapped_column(String(16))           # front / back
    position: Mapped[int] = mapped_column(Integer, default=0)
    levels_count: Mapped[int] = mapped_column(Integer, default=8)
    section: Mapped[Section] = relationship(back_populates="shelves", lazy="joined")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_store_title_author", "store_id", "title_norm", "author_norm"),
        Index("ix_items_store_kind", "store_id", "kind"),
        Index(
            "ix_items_search_trgm", "search_norm",
            postgresql_using="gin", postgresql_ops={"search_norm": "gin_trgm_ops"},
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(32), default="other")
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255), default="")
    title_norm: Mapped[str] = mapped_column(String(255))
    author_norm: Mapped[str] = mapped_column(String(255), default="")
    search_norm: Mapped[str] = mapped_column(String(512))
    # Vizual xotira: rang nomlari, hex ranglar, shakl, muqova tavsifi
    colors: Mapped[list] = mapped_column(JSON, default=list)
    color_hex: Mapped[list] = mapped_column(JSON, default=list)
    shape: Mapped[str] = mapped_column(String(64), default="")
    visual_description: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Placement(Base):
    __tablename__ = "placements"
    __table_args__ = (
        UniqueConstraint("item_id", "shelf_id", "level", name="uq_placement_item_shelf_level"),
        Index("ix_placements_shelf_level", "shelf_id", "level"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id", ondelete="CASCADE"))
    level: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="in_stock")
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ItemImage(Base):
    __tablename__ = "item_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    thumbnail: Mapped[bytes] = mapped_column(LargeBinary)
    source: Mapped[str] = mapped_column(String(32), default="shelf_photo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RecognitionBatch(Base):
    """AI tanigan, lekin hali tasdiqlanmagan narsalar (bot va WebApp uchun umumiy)."""
    __tablename__ = "recognition_batches"
    __table_args__ = (Index("ix_batches_user_status", "user_id", "status"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id", ondelete="CASCADE"))
    level: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    items: Mapped[list] = mapped_column(JSON, default=list)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
