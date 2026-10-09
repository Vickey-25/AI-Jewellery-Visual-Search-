"""create products table

Revision ID: 0001
Revises:
Create Date: 2026-10-01
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

INDEXED = ["category", "material", "purity", "price", "occasion", "is_active"]


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("material", sa.String(50), nullable=False),
        sa.Column("purity", sa.String(20)),
        sa.Column("weight", sa.Numeric(10, 2)),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("stone_type", sa.String(50)),
        sa.Column("colour", sa.String(50)),
        sa.Column("occasion", sa.String(50)),
        sa.Column("image_filename", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_products_product_code", "products", ["product_code"], unique=True)
    for column in INDEXED:
        op.create_index(f"ix_products_{column}", "products", [column])


def downgrade() -> None:
    for column in INDEXED:
        op.drop_index(f"ix_products_{column}", table_name="products")
    op.drop_index("ix_products_product_code", table_name="products")
    op.drop_table("products")
