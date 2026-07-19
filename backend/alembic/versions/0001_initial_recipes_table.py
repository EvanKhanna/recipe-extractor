"""initial recipes table

Revision ID: 0001
Revises: 
Create Date: 2026-07-19 14:17:16.422714

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        # Clerk user id (the `sub` claim); every recipe belongs to one user.
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # JSON columns. Defaults are applied by the ORM in Python, not the DB.
        sa.Column("ingredients", sa.JSON(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("servings", sa.String(length=100), nullable=True),
        sa.Column("prep_time", sa.String(length=100), nullable=True),
        sa.Column("cook_time", sa.String(length=100), nullable=True),
        # Provenance: "video" | "image", plus the original url when applicable.
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Recipes are always queried by owner, so user_id is indexed (models.py index=True).
    op.create_index("ix_recipes_user_id", "recipes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_recipes_user_id", table_name="recipes")
    op.drop_table("recipes")
