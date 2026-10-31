import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import ProductImage


def get(db: Session, image_id: uuid.UUID) -> ProductImage | None:
    return db.get(ProductImage, image_id)


def list_for_product(db: Session, product_id: uuid.UUID) -> list[ProductImage]:
    stmt = (
        select(ProductImage)
        .where(ProductImage.product_id == product_id)
        .order_by(ProductImage.sort_order, ProductImage.created_at)
    )
    return list(db.scalars(stmt))


def count_for_product(db: Session, product_id: uuid.UUID) -> int:
    stmt = (
        select(func.count()).select_from(ProductImage).where(ProductImage.product_id == product_id)
    )
    return db.scalar(stmt) or 0


def clear_primary(db: Session, product_id: uuid.UUID) -> None:
    """Needed before setting a new primary: a partial unique index allows only one per product."""
    db.execute(
        update(ProductImage)
        .where(ProductImage.product_id == product_id, ProductImage.is_primary)
        .values(is_primary=False)
    )
