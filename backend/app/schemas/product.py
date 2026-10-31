import uuid
from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from app.models import Product, ProductVariant
from app.models.enums import ProductStatus, Weight
from app.schemas.category import CategoryOut
from app.schemas.common import MoneyIn, PatchModel, Slug


def discount_percent(price: Decimal, compare_at: Decimal | None) -> int:
    if compare_at is None or compare_at <= price:
        return 0
    return int(((compare_at - price) / compare_at * 100).quantize(Decimal(1)))


# ---------- inventory ----------
class InventorySet(BaseModel):
    quantity: int = Field(ge=0)
    low_stock_threshold: int | None = Field(default=None, ge=0)


class InventoryAdjust(BaseModel):
    delta: int
    note: str | None = Field(default=None, max_length=200)

    @field_validator("delta")
    @classmethod
    def _non_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("delta must not be 0")
        return v


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quantity: int
    reserved: int
    low_stock_threshold: int

    @computed_field
    @property
    def available(self) -> int:
        return self.quantity - self.reserved


# ---------- variants ----------
class VariantCreate(BaseModel):
    weight: Weight
    price: MoneyIn
    compare_at_price: MoneyIn | None = None
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool = True
    quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)

    @model_validator(mode="after")
    def _compare_at(self) -> Self:
        if self.compare_at_price is not None and self.compare_at_price < self.price:
            raise ValueError("compare_at_price must be >= price")
        return self


class VariantUpdate(PatchModel):
    """Weight is immutable: delete and re-create the variant to change it."""

    non_nullable: ClassVar[set[str]] = {"price", "is_active"}

    price: MoneyIn | None = None
    compare_at_price: MoneyIn | None = None
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None


class VariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    weight: Weight
    price: Decimal
    compare_at_price: Decimal | None
    sku: str | None
    is_active: bool
    inventory: InventoryOut | None

    @computed_field
    @property
    def discount_percent(self) -> int:
        return discount_percent(self.price, self.compare_at_price)


class VariantPublic(BaseModel):
    id: uuid.UUID
    weight: Weight
    price: Decimal
    compare_at_price: Decimal | None
    discount_percent: int
    in_stock: bool
    available_quantity: int

    @classmethod
    def from_variant(cls, v: ProductVariant) -> Self:
        available = v.inventory.quantity - v.inventory.reserved if v.inventory else 0
        return cls(
            id=v.id,
            weight=v.weight,
            price=v.price,
            compare_at_price=v.compare_at_price,
            discount_percent=discount_percent(v.price, v.compare_at_price),
            in_stock=available > 0,
            available_quantity=max(available, 0),
        )


# ---------- products ----------
class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    alt_text: str | None
    sort_order: int
    is_primary: bool


class ProductFields(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    name_te: str | None = Field(default=None, max_length=200)
    short_description: str | None = Field(default=None, max_length=300)
    short_description_te: str | None = Field(default=None, max_length=300)
    description: str | None = None
    description_te: str | None = None
    ingredients: str | None = None
    ingredients_te: str | None = None
    preparation: str | None = None
    preparation_te: str | None = None
    storage_instructions: str | None = None
    storage_instructions_te: str | None = None
    shelf_life: str | None = Field(default=None, max_length=100)
    badges: list[str] = Field(default_factory=list, max_length=10)
    status: ProductStatus = ProductStatus.ACTIVE
    is_featured: bool = False
    is_best_seller: bool = False
    is_new_arrival: bool = False
    seo_title: str | None = Field(default=None, max_length=200)
    seo_description: str | None = Field(default=None, max_length=320)

    @field_validator("badges")
    @classmethod
    def _badges(cls, v: list[str]) -> list[str]:
        if any(not b.strip() or len(b) > 40 for b in v):
            raise ValueError("badges must be non-empty strings up to 40 characters")
        return v


class ProductCreate(ProductFields):
    slug: Slug | None = None  # generated from the name when omitted
    category_id: uuid.UUID
    variants: list[VariantCreate] = Field(default_factory=list, max_length=len(Weight))

    @model_validator(mode="after")
    def _unique_weights(self) -> Self:
        weights = [v.weight for v in self.variants]
        if len(weights) != len(set(weights)):
            raise ValueError("each weight may appear only once")
        return self


class ProductUpdate(PatchModel):
    non_nullable: ClassVar[set[str]] = {
        "slug",
        "category_id",
        "name",
        "badges",
        "status",
        "is_featured",
        "is_best_seller",
        "is_new_arrival",
    }

    slug: Slug | None = None
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    name_te: str | None = Field(default=None, max_length=200)
    short_description: str | None = Field(default=None, max_length=300)
    short_description_te: str | None = Field(default=None, max_length=300)
    description: str | None = None
    description_te: str | None = None
    ingredients: str | None = None
    ingredients_te: str | None = None
    preparation: str | None = None
    preparation_te: str | None = None
    storage_instructions: str | None = None
    storage_instructions_te: str | None = None
    shelf_life: str | None = Field(default=None, max_length=100)
    badges: list[str] | None = Field(default=None, max_length=10)
    status: ProductStatus | None = None
    is_featured: bool | None = None
    is_best_seller: bool | None = None
    is_new_arrival: bool | None = None
    seo_title: str | None = Field(default=None, max_length=200)
    seo_description: str | None = Field(default=None, max_length=320)


class ProductOut(ProductFields):
    """Admin view: everything, including inactive variants and stock numbers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    category_id: uuid.UUID
    sold_count: int
    images: list[ProductImageOut]
    variants: list[VariantOut]
    created_at: datetime
    updated_at: datetime


class ProductPublic(BaseModel):
    """Storefront view: active variants only, availability instead of raw stock."""

    id: uuid.UUID
    slug: str
    name: str
    name_te: str | None
    short_description: str | None
    short_description_te: str | None
    description: str | None
    description_te: str | None
    ingredients: str | None
    ingredients_te: str | None
    preparation: str | None
    preparation_te: str | None
    storage_instructions: str | None
    storage_instructions_te: str | None
    shelf_life: str | None
    badges: list[str]
    is_featured: bool
    is_best_seller: bool
    is_new_arrival: bool
    seo_title: str | None
    seo_description: str | None
    category: CategoryOut
    images: list[ProductImageOut]
    variants: list[VariantPublic]
    in_stock: bool
    min_price: Decimal | None
    max_discount_percent: int

    @classmethod
    def from_product(cls, p: Product) -> Self:
        variants = sorted(
            (VariantPublic.from_variant(v) for v in p.variants if v.is_active),
            key=lambda v: v.price,
        )
        return cls(
            **{
                f: getattr(p, f)
                for f in cls.model_fields
                if hasattr(p, f)
                and f
                not in {
                    "category",
                    "images",
                    "variants",
                }
            },
            category=CategoryOut.model_validate(p.category),
            images=[ProductImageOut.model_validate(i) for i in p.images],
            variants=variants,
            in_stock=any(v.in_stock for v in variants),
            min_price=variants[0].price if variants else None,
            max_discount_percent=max((v.discount_percent for v in variants), default=0),
        )


class LowStockItem(BaseModel):
    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    weight: Weight
    quantity: int
    reserved: int
    available: int
    low_stock_threshold: int
