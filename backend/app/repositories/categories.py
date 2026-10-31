import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, Product


def list_all(db: Session, *, active_only: bool = False) -> list[Category]:
    stmt = select(Category).order_by(Category.sort_order, Category.name)
    if active_only:
        stmt = stmt.where(Category.is_active)
    return list(db.scalars(stmt))


def get(db: Session, category_id: uuid.UUID) -> Category | None:
    return db.get(Category, category_id)


def slug_taken(db: Session, slug: str, *, exclude_id: uuid.UUID | None = None) -> bool:
    stmt = select(Category.id).where(Category.slug == slug)
    if exclude_id:
        stmt = stmt.where(Category.id != exclude_id)
    return db.scalar(stmt) is not None


def product_count(db: Session, category_id: uuid.UUID) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(Product).where(Product.category_id == category_id)
        )
        or 0
    )
