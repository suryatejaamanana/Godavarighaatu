import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import MONEY, Base, Money, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ComboRuleType, DiscountType
from app.models.types import str_enum


class Coupon(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coupons"
    __table_args__ = (
        CheckConstraint("value > 0", name="value_positive"),
        CheckConstraint("type <> 'percent' OR value <= 100", name="percent_at_most_100"),
        CheckConstraint("min_purchase >= 0", name="min_purchase_non_negative"),
        CheckConstraint("usage_limit IS NULL OR usage_limit > 0", name="usage_limit_positive"),
        CheckConstraint("used_count >= 0", name="used_count_non_negative"),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at", name="date_range"
        ),
    )

    code: Mapped[str] = mapped_column(
        String(40), unique=True
    )  # stored upper-case by the service layer
    description: Mapped[str | None] = mapped_column(String(300))
    type: Mapped[DiscountType] = mapped_column(str_enum(DiscountType, "coupon_type"))
    value: Mapped[Money]
    min_purchase: Mapped[Money] = mapped_column(MONEY, default=Decimal(0), server_default="0")
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class ComboOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """fixed_products: bundle of listed products. any_n: customer picks `item_count` from eligible items."""

    __tablename__ = "combo_offers"
    __table_args__ = (
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint(
            "(rule_type = 'any_n' AND item_count IS NOT NULL AND item_count > 0) OR (rule_type = 'fixed_products' AND item_count IS NULL)",
            name="item_count_matches_rule",
        ),
    )

    slug: Mapped[str] = mapped_column(String(160), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    name_te: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    description_te: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    rule_type: Mapped[ComboRuleType] = mapped_column(str_enum(ComboRuleType, "combo_rule_type"))
    item_count: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[Money]
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    items: Mapped[list["ComboOfferItem"]] = relationship(
        back_populates="combo", cascade="all, delete-orphan"
    )


class ComboOfferItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A specific product, or (for any_n combos) a whole eligible category."""

    __tablename__ = "combo_offer_items"
    __table_args__ = (
        CheckConstraint(
            "(product_id IS NOT NULL) <> (category_id IS NOT NULL)", name="product_xor_category"
        ),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index(
            "uq_combo_offer_items_combo_product",
            "combo_id",
            "product_id",
            unique=True,
            postgresql_where=text("product_id IS NOT NULL"),
        ),
        Index(
            "uq_combo_offer_items_combo_category",
            "combo_id",
            "category_id",
            unique=True,
            postgresql_where=text("category_id IS NOT NULL"),
        ),
    )

    combo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("combo_offers.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    combo: Mapped[ComboOffer] = relationship(back_populates="items")


__all__ = ["ComboOffer", "ComboOfferItem", "Coupon"]
