import uuid
from enum import StrEnum

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Category, Inventory, Product, ProductVariant
from app.models.enums import ProductStatus


class ProductSort(StrEnum):
    NEWEST = "newest"
    POPULAR = "popular"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


_LOAD = (
    selectinload(Product.category),
    selectinload(Product.images),
    selectinload(Product.variants).selectinload(ProductVariant.inventory),
)


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


def _filtered(
    *,
    q: str | None,
    category_slug: str | None,
    category_id: uuid.UUID | None,
    statuses: list[ProductStatus],
    public_only: bool,
    flags: dict[str, bool],
) -> Select:
    stmt = select(Product).where(Product.status.in_(statuses))
    if public_only:
        stmt = stmt.join(Category).where(Category.is_active)
    if q:
        like = f"%{_escape_like(q.strip())}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.name_te.ilike(like)))
    if category_slug:
        stmt = stmt.where(Product.category.has(Category.slug == category_slug))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    for column, wanted in flags.items():
        if wanted:
            stmt = stmt.where(getattr(Product, column))
    return stmt


def search(
    db: Session,
    *,
    q: str | None = None,
    category_slug: str | None = None,
    category_id: uuid.UUID | None = None,
    statuses: list[ProductStatus],
    public_only: bool = False,
    flags: dict[str, bool] | None = None,
    sort: ProductSort = ProductSort.NEWEST,
    offset: int = 0,
    limit: int = 12,
) -> tuple[list[Product], int]:
    stmt = _filtered(
        q=q,
        category_slug=category_slug,
        category_id=category_id,
        statuses=statuses,
        public_only=public_only,
        flags=flags or {},
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort in (ProductSort.PRICE_ASC, ProductSort.PRICE_DESC):
        min_price = (
            select(ProductVariant.product_id, func.min(ProductVariant.price).label("min_price"))
            .where(ProductVariant.is_active)
            .group_by(ProductVariant.product_id)
            .subquery()
        )
        stmt = stmt.outerjoin(min_price, min_price.c.product_id == Product.id)
        col = min_price.c.min_price
        order = [
            col.asc().nulls_last() if sort == ProductSort.PRICE_ASC else col.desc().nulls_last()
        ]
    elif sort == ProductSort.POPULAR:
        order = [Product.sold_count.desc(), Product.created_at.desc()]
    else:
        order = [Product.created_at.desc()]

    stmt = stmt.order_by(*order, Product.id).offset(offset).limit(limit).options(*_LOAD)
    return list(db.scalars(stmt)), total


def get(db: Session, product_id: uuid.UUID) -> Product | None:
    return db.scalar(select(Product).where(Product.id == product_id).options(*_LOAD))


def get_by_slug(db: Session, slug: str) -> Product | None:
    return db.scalar(select(Product).where(Product.slug == slug).options(*_LOAD))


def slug_taken(db: Session, slug: str, *, exclude_id: uuid.UUID | None = None) -> bool:
    stmt = select(Product.id).where(Product.slug == slug)
    if exclude_id:
        stmt = stmt.where(Product.id != exclude_id)
    return db.scalar(stmt) is not None


def related(db: Session, product: Product, limit: int = 4) -> list[Product]:
    stmt = (
        select(Product)
        .join(Category)
        .where(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.status == ProductStatus.ACTIVE,
            Category.is_active,
        )
        .order_by(Product.sold_count.desc(), Product.created_at.desc())
        .limit(limit)
        .options(*_LOAD)
    )
    return list(db.scalars(stmt))


# ---------- variants / inventory ----------
def get_variant(db: Session, variant_id: uuid.UUID) -> ProductVariant | None:
    return db.scalar(
        select(ProductVariant)
        .where(ProductVariant.id == variant_id)
        .options(selectinload(ProductVariant.inventory))
    )


def sku_taken(db: Session, sku: str, *, exclude_id: uuid.UUID | None = None) -> bool:
    stmt = select(ProductVariant.id).where(ProductVariant.sku == sku)
    if exclude_id:
        stmt = stmt.where(ProductVariant.id != exclude_id)
    return db.scalar(stmt) is not None


def low_stock(db: Session) -> list[tuple[ProductVariant, Product, Inventory]]:
    stmt = (
        select(ProductVariant, Product, Inventory)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Inventory, Inventory.variant_id == ProductVariant.id)
        .where(
            Product.status != ProductStatus.ARCHIVED,
            ProductVariant.is_active,
            Inventory.quantity - Inventory.reserved <= Inventory.low_stock_threshold,
        )
        .order_by(Inventory.quantity - Inventory.reserved, Product.name)
    )
    return [tuple(r) for r in db.execute(stmt)]


def count_by_status(db: Session) -> dict[ProductStatus, int]:
    rows = db.execute(select(Product.status, func.count()).group_by(Product.status))
    return {ProductStatus(status): n for status, n in rows}


def count_out_of_stock(db: Session) -> int:
    stmt = (
        select(func.count())
        .select_from(ProductVariant)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Inventory, Inventory.variant_id == ProductVariant.id)
        .where(
            Product.status == ProductStatus.ACTIVE,
            ProductVariant.is_active,
            Inventory.quantity - Inventory.reserved <= 0,
        )
    )
    return db.scalar(stmt) or 0
