import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import MONEY, Base, Money, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import OrderStatus, PaymentStatus, ShipmentStatus, Weight
from app.models.types import str_enum


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="subtotal_non_negative"),
        CheckConstraint(
            "discount_total >= 0 AND discount_total <= subtotal", name="discount_range"
        ),
        CheckConstraint("total >= 0", name="total_non_negative"),
        Index("ix_orders_order_status_created_at", "order_status", "created_at"),
        Index("ix_orders_payment_status", "payment_status"),
    )

    order_number: Mapped[str] = mapped_column(String(32), unique=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    coupon_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("coupons.id", ondelete="SET NULL"), index=True
    )
    coupon_code: Mapped[str | None] = mapped_column(String(40))  # snapshot

    order_status: Mapped[OrderStatus] = mapped_column(
        str_enum(OrderStatus, "order_status"),
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        str_enum(PaymentStatus, "payment_status"),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )

    subtotal: Mapped[Money]
    discount_total: Mapped[Money] = mapped_column(MONEY, default=Decimal(0), server_default="0")
    total: Mapped[Money]

    # Delivery details are snapshots: later edits to customer/address must not alter past orders.
    ship_full_name: Mapped[str] = mapped_column(String(120))
    ship_mobile: Mapped[str] = mapped_column(String(15), index=True)
    ship_email: Mapped[str | None] = mapped_column(String(254))
    ship_house: Mapped[str] = mapped_column(String(120))
    ship_street: Mapped[str] = mapped_column(String(200))
    ship_village_city: Mapped[str] = mapped_column(String(120))
    ship_district: Mapped[str] = mapped_column(String(120))
    ship_state: Mapped[str] = mapped_column(String(120))
    ship_pin_code: Mapped[str] = mapped_column(String(6))
    delivery_instructions: Mapped[str | None] = mapped_column(Text)
    admin_notes: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at",
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    shipments: Mapped[list["Shipment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Historical record: name, weight and unit price are copied at purchase time."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), index=True
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL"), index=True
    )
    product_name: Mapped[str] = mapped_column(String(200))
    product_name_te: Mapped[str | None] = mapped_column(String(200))
    weight: Mapped[Weight] = mapped_column(str_enum(Weight, "order_item_weight"))
    unit_price: Mapped[Money]
    quantity: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[Money]

    order: Mapped[Order] = relationship(back_populates="items")


class OrderStatusHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "order_status_history"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[OrderStatus | None] = mapped_column(
        str_enum(OrderStatus, "history_from_status")
    )
    to_status: Mapped[OrderStatus] = mapped_column(str_enum(OrderStatus, "history_to_status"))
    changed_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(Text)

    order: Mapped[Order] = relationship(back_populates="status_history")


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Provider-agnostic. 'manual' until a gateway is chosen; raw_payload is for future webhooks."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        Index("ix_payments_provider_provider_reference", "provider", "provider_reference"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(40), default="manual", server_default="manual")
    method: Mapped[str | None] = mapped_column(String(40))
    amount: Mapped[Money]
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    status: Mapped[PaymentStatus] = mapped_column(
        str_enum(PaymentStatus, "payments_status"),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    provider_reference: Mapped[str | None] = mapped_column(String(120))
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped[Order] = relationship(back_populates="payments")


class Shipment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Manual tracking now; provider/provider_reference let a courier integration plug in later."""

    __tablename__ = "shipments"
    __table_args__ = (
        Index("ix_shipments_provider_provider_reference", "provider", "provider_reference"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(40), default="manual", server_default="manual")
    carrier: Mapped[str | None] = mapped_column(String(80))
    tracking_number: Mapped[str | None] = mapped_column(String(120))
    tracking_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ShipmentStatus] = mapped_column(
        str_enum(ShipmentStatus, "shipment_status"),
        default=ShipmentStatus.PENDING,
        server_default=ShipmentStatus.PENDING.value,
    )
    provider_reference: Mapped[str | None] = mapped_column(String(120))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped[Order] = relationship(back_populates="shipments")
