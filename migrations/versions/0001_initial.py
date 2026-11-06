"""Boshlang'ich sxema: users, stores, members, sections, shelves, items, placements, images, batches.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-06
"""
import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

_TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    is_pg = op.get_bind().dialect.name == "postgresql"
    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
    )

    op.create_table(
        "store_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.UniqueConstraint("store_id", "user_id", name="uq_member_store_user"),
    )
    op.create_index("ix_store_members_store_id", "store_members", ["store_id"])
    op.create_index("ix_store_members_user_id", "store_members", ["user_id"])

    op.create_table(
        "sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("store_id", "code", name="uq_section_store_code"),
    )
    op.create_index("ix_sections_store_id", "sections", ["store_id"])

    op.create_table(
        "shelves",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("section_id", sa.Integer(), sa.ForeignKey("sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("side", sa.String(16), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("levels_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("section_id", "code", name="uq_shelf_section_code"),
    )
    op.create_index("ix_shelves_section_id", "shelves", ["section_id"])

    _create_items(is_pg)
    _create_placements_and_rest()


def _create_items(is_pg: bool) -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("title_norm", sa.String(255), nullable=False),
        sa.Column("author_norm", sa.String(255), nullable=False),
        sa.Column("search_norm", sa.String(512), nullable=False),
        sa.Column("colors", sa.JSON(), nullable=False),
        sa.Column("color_hex", sa.JSON(), nullable=False),
        sa.Column("shape", sa.String(64), nullable=False),
        sa.Column("visual_description", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
    )
    op.create_index("ix_items_store_title_author", "items", ["store_id", "title_norm", "author_norm"])
    op.create_index("ix_items_store_kind", "items", ["store_id", "kind"])
    if is_pg:
        op.create_index("ix_items_search_trgm", "items", ["search_norm"],
                        postgresql_using="gin", postgresql_ops={"search_norm": "gin_trgm_ops"})
    else:
        op.create_index("ix_items_search_trgm", "items", ["search_norm"])


def _create_placements_and_rest() -> None:
    op.create_table(
        "placements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shelf_id", sa.Integer(), sa.ForeignKey("shelves.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", _TS, nullable=False),
        sa.UniqueConstraint("item_id", "shelf_id", "level", name="uq_placement_item_shelf_level"),
    )
    op.create_index("ix_placements_item_id", "placements", ["item_id"])
    op.create_index("ix_placements_shelf_level", "placements", ["shelf_id", "level"])

    op.create_table(
        "item_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("thumbnail", sa.LargeBinary(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
    )
    op.create_index("ix_item_images_item_id", "item_images", ["item_id"])

    op.create_table(
        "recognition_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shelf_id", sa.Integer(), sa.ForeignKey("shelves.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("avg_confidence", sa.Float(), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
    )
    op.create_index("ix_batches_user_status", "recognition_batches", ["user_id", "status"])


def downgrade() -> None:
    for table in ("recognition_batches", "item_images", "placements", "items",
                  "shelves", "sections", "store_members", "stores", "users"):
        op.drop_table(table)
