from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Clerk user id (the `sub` claim). Every recipe belongs to one user.
    user_id: Mapped[str] = mapped_column(String(255), index=True)

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stored as JSON: ingredients = [{"quantity": str|None, "item": str}, ...]
    ingredients: Mapped[list] = mapped_column(JSON, default=list)
    # steps = ["step 1", "step 2", ...]
    steps: Mapped[list] = mapped_column(JSON, default=list)

    servings: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prep_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cook_time: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Provenance
    source_type: Mapped[str] = mapped_column(String(50))  # "video" | "image"
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
