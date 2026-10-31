import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.models import Inventory, Product, ProductVariant
from app.models.enums import ProductStatus
from app.repositories import categories as category_repo
from app.repositories import products as repo
from app.repositories.products import ProductSort
from app.schemas.common import slugify
from app.schemas.product import (
    DashboardSummary,
    InventoryAdjust,
    InventorySet,
    LowStockItem,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)

ALL_STATUSES = list(ProductStatus)


# ---------- products ----------
def list_public(db: Session, *, q, category_slug, sort: ProductSort, page: int, page_size: int):
    return repo.search(
        db,
        q=q,
        category_slug=category_slug,
        statuses=[ProductStatus.ACTIVE],
        public_only=True,
        sort=sort,
        offset=(page - 1) * page_size,
        limit=page_size,
    )


def list_admin(
    db: Session, *, q, category_id, status: ProductStatus | None, sort: ProductSort, page, page_size
):
    return repo.search(
        db,
        q=q,
        category_id=category_id,
        statuses=[status] if status else ALL_STATUSES,
        sort=sort,
        offset=(page - 1) * page_size,
        limit=page_size,
    )


def get_public_by_slug(db: Session, slug: str) -> Product:
    product = repo.get_by_slug(db, slug)
    if product is None or product.status != ProductStatus.ACTIVE or not product.category.is_active:
        raise NotFoundError("Product not found.")
    return product


def get_related(db: Session, product: Product) -> list[Product]:
    return repo.related(db, product)


def get_product(db: Session, product_id: uuid.UUID) -> Product:
    product = repo.get(db, product_id)
    if product is None:
        raise NotFoundError("Product not found.")
    return product


def _require_category(db: Session, category_id: uuid.UUID) -> None:
    if category_repo.get(db, category_id) is None:
        raise BusinessRuleError("Category does not exist.")


def _check_sku(db: Session, sku: str | None, exclude_id: uuid.UUID | None = None) -> None:
    if sku and repo.sku_taken(db, sku, exclude_id=exclude_id):
        raise ConflictError(f"SKU '{sku}' is already in use.")


def _new_variant(data: VariantCreate) -> ProductVariant:
    variant = ProductVariant(
        **data.model_dump(exclude={"quantity", "low_stock_threshold"}),
    )
    variant.inventory = Inventory(
        quantity=data.quantity, low_stock_threshold=data.low_stock_threshold
    )
    return variant


def create_product(db: Session, data: ProductCreate) -> Product:
    slug = data.slug or slugify(data.name)
    if not slug:
        raise BusinessRuleError("Could not generate a slug from the name; provide one.")
    if repo.slug_taken(db, slug):
        raise ConflictError(f"Product slug '{slug}' already exists.")
    _require_category(db, data.category_id)
    skus = [v.sku for v in data.variants if v.sku]
    if len(skus) != len(set(skus)):
        raise ConflictError("Duplicate SKU in request.")
    for sku in skus:
        _check_sku(db, sku)

    product = Product(**data.model_dump(exclude={"slug", "variants"}), slug=slug)
    product.variants = [_new_variant(v) for v in data.variants]
    db.add(product)
    db.commit()
    return get_product(db, product.id)


def update_product(db: Session, product_id: uuid.UUID, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    changes = data.model_dump(exclude_unset=True)
    if "slug" in changes and repo.slug_taken(db, changes["slug"], exclude_id=product.id):
        raise ConflictError(f"Product slug '{changes['slug']}' already exists.")
    if "category_id" in changes:
        _require_category(db, changes["category_id"])
    for field, value in changes.items():
        setattr(product, field, value)
    db.commit()
    return get_product(db, product.id)


def set_status(db: Session, product_id: uuid.UUID, status: ProductStatus) -> Product:
    product = get_product(db, product_id)
    product.status = status
    db.commit()
    return get_product(db, product.id)


# ---------- variants ----------
def list_variants(db: Session, product_id: uuid.UUID) -> list[ProductVariant]:
    return sorted(get_product(db, product_id).variants, key=lambda v: v.price)


def get_variant(db: Session, variant_id: uuid.UUID) -> ProductVariant:
    variant = repo.get_variant(db, variant_id)
    if variant is None:
        raise NotFoundError("Variant not found.")
    return variant


def create_variant(db: Session, product_id: uuid.UUID, data: VariantCreate) -> ProductVariant:
    product = get_product(db, product_id)
    if any(v.weight == data.weight for v in product.variants):
        raise ConflictError(f"This product already has a {data.weight.value} variant.")
    _check_sku(db, data.sku)
    variant = _new_variant(data)
    variant.product_id = product.id
    db.add(variant)
    db.commit()
    return get_variant(db, variant.id)


def update_variant(db: Session, variant_id: uuid.UUID, data: VariantUpdate) -> ProductVariant:
    variant = get_variant(db, variant_id)
    changes = data.model_dump(exclude_unset=True)
    if "sku" in changes:
        _check_sku(db, changes["sku"], exclude_id=variant.id)
    price: Decimal = changes.get("price", variant.price)
    compare_at = changes.get("compare_at_price", variant.compare_at_price)
    if compare_at is not None and compare_at < price:
        raise BusinessRuleError("compare_at_price must be >= price.")
    for field, value in changes.items():
        setattr(variant, field, value)
    db.commit()
    return get_variant(db, variant.id)


def delete_variant(db: Session, variant_id: uuid.UUID) -> None:
    variant = get_variant(db, variant_id)
    # Past orders keep their own name/weight/price snapshot, so deletion is safe for history.
    db.delete(variant)
    db.commit()


# ---------- inventory ----------
def _inventory(db: Session, variant_id: uuid.UUID) -> Inventory:
    variant = get_variant(db, variant_id)
    if variant.inventory is None:  # defensive: created together with the variant
        variant.inventory = Inventory(quantity=0)
        db.flush()
    db.refresh(
        variant.inventory, with_for_update=True
    )  # row lock: concurrent adjustments serialize
    return variant.inventory


def set_inventory(db: Session, variant_id: uuid.UUID, data: InventorySet) -> ProductVariant:
    inv = _inventory(db, variant_id)
    if data.quantity < inv.reserved:
        raise BusinessRuleError(
            f"Quantity cannot be below the {inv.reserved} units already reserved."
        )
    inv.quantity = data.quantity
    if data.low_stock_threshold is not None:
        inv.low_stock_threshold = data.low_stock_threshold
    db.commit()
    return get_variant(db, variant_id)


def adjust_inventory(db: Session, variant_id: uuid.UUID, data: InventoryAdjust) -> ProductVariant:
    inv = _inventory(db, variant_id)
    new_quantity = inv.quantity + data.delta
    if new_quantity < 0:
        raise BusinessRuleError("Adjustment would make stock negative.")
    if new_quantity < inv.reserved:
        raise BusinessRuleError(
            f"Quantity cannot be below the {inv.reserved} units already reserved."
        )
    inv.quantity = new_quantity
    db.commit()
    return get_variant(db, variant_id)


def low_stock(db: Session) -> list[LowStockItem]:
    return [
        LowStockItem(
            variant_id=v.id,
            product_id=p.id,
            product_name=p.name,
            weight=v.weight,
            quantity=i.quantity,
            reserved=i.reserved,
            available=i.quantity - i.reserved,
            low_stock_threshold=i.low_stock_threshold,
        )
        for v, p, i in repo.low_stock(db)
    ]


def dashboard_summary(db: Session) -> DashboardSummary:
    by_status = repo.count_by_status(db)
    return DashboardSummary(
        products_total=sum(by_status.values()),
        products_active=by_status.get(ProductStatus.ACTIVE, 0),
        products_inactive=by_status.get(ProductStatus.INACTIVE, 0),
        products_archived=by_status.get(ProductStatus.ARCHIVED, 0),
        categories_total=len(category_repo.list_all(db)),
        variants_out_of_stock=repo.count_out_of_stock(db),
        variants_low_stock=len(repo.low_stock(db)),
    )
