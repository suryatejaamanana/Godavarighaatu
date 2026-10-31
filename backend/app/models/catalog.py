import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import MONEY, Base, Money, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ProductStatus, Weight
from app.models.types import str_enum


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    slug: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    name_te: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    description_te: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category_id_status", "category_id", "status"),
        Index(
            "ix_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        CheckConstraint("sold_count >= 0", name="sold_count_non_negative"),
    )

    slug: Mapped[str] = mapped_column(String(160), unique=True)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(200))
    name_te: Mapped[str | None] = mapped_column(String(200))
    short_description: Mapped[str | None] = mapped_column(String(300))
    short_description_te: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    description_te: Mapped[str | None] = mapped_column(Text)
    ingredients: Mapped[str | None] = mapped_column(Text)
    ingredients_te: Mapped[str | None] = mapped_column(Text)
    preparation: Mapped[str | None] = mapped_column(Text)
    preparation_te: Mapped[str | None] = mapped_column(Text)
    storage_instructions: Mapped[str | None] = mapped_column(Text)
    storage_instructions_te: Mapped[str | None] = mapped_column(Text)
    shelf_life: Mapped[str | None] = mapped_column(String(100))
    badges: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), default=list, server_default=text("'{}'")
    )
    status: Mapped[ProductStatus] = mapped_column(
        str_enum(ProductStatus, "product_status"),
        default=ProductStatus.ACTIVE,
        server_default=ProductStatus.ACTIVE.value,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    is_best_seller: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    is_new_arrival: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    sold_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # popularity
    seo_title: Mapped[str | None] = mapped_column(String(200))
    seo_description: Mapped[str | None] = mapped_column(String(320))

    category: Mapped[Category] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.sort_order"
    )
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")


class ProductImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_images"
    __table_args__ = (
        Index("ix_product_images_product_id", "product_id"),
        # at most one primary image per product
        Index(
            "uq_product_images_primary",
            "product_id",
            unique=True,
            postgresql_where=text("is_primary"),
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(500))
    storage_path: Mapped[str | None] = mapped_column(String(500))
    alt_text: Mapped[str | None] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    product: Mapped[Product] = relationship(back_populates="images")


class ProductVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("product_id", "weight", name="uq_product_variants_product_id_weight"),
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint(
            "compare_at_price IS NULL OR compare_at_price >= price",
            name="compare_at_price_gte_price",
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    weight: Mapped[Weight] = mapped_column(str_enum(Weight, "variant_weight"))
    price: Mapped[Money]
    compare_at_price: Mapped[Decimal | None] = mapped_column(MONEY)
    sku: Mapped[str | None] = mapped_column(String(64), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))

    product: Mapped[Product] = relationship(back_populates="variants")
    inventory: Mapped["Inventory"] = relationship(
        back_populates="variant", cascade="all, delete-orphan", uselist=False
    )


class Inventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("reserved >= 0 AND reserved <= quantity", name="reserved_within_quantity"),
        CheckConstraint("low_stock_threshold >= 0", name="low_stock_threshold_non_negative"),
    )

    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), unique=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    reserved: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, server_default="5")

    variant: Mapped[ProductVariant] = relationship(back_populates="inventory")


class Review(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
        Index("ix_reviews_product_id_is_approved", "product_id", "is_approved"),
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE")
    )
    customer_name: Mapped[str] = mapped_column(String(120))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    product: Mapped[Product | None] = relationship(back_populates="reviews")


__all__ = [
    "Category",
    "Inventory",
    "Product",
    "ProductImage",
    "ProductVariant",
    "Review",
]
