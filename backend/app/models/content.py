from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Banner(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "banners"
    __table_args__ = (
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at", name="date_range"
        ),
        Index("ix_banners_is_active_sort_order", "is_active", "sort_order"),
    )

    title: Mapped[str | None] = mapped_column(String(200))
    title_te: Mapped[str | None] = mapped_column(String(200))
    subtitle: Mapped[str | None] = mapped_column(String(300))
    subtitle_te: Mapped[str | None] = mapped_column(String(300))
    image_url: Mapped[str] = mapped_column(String(500))
    mobile_image_url: Mapped[str | None] = mapped_column(String(500))
    link_url: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WebsiteSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Key/value business content: brand name, tagline, contact, WhatsApp number, policies, ..."""

    __tablename__ = "website_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[dict | list | str | int | bool | None] = mapped_column(JSONB)
