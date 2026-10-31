import uuid

from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.models import Category
from app.repositories import categories as repo
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.common import slugify


def list_categories(db: Session, *, active_only: bool) -> list[Category]:
    return repo.list_all(db, active_only=active_only)


def get_category(db: Session, category_id: uuid.UUID) -> Category:
    category = repo.get(db, category_id)
    if category is None:
        raise NotFoundError("Category not found.")
    return category


def create_category(db: Session, data: CategoryCreate) -> Category:
    slug = data.slug or slugify(data.name)
    if not slug:
        raise BusinessRuleError("Could not generate a slug from the name; provide one.")
    if repo.slug_taken(db, slug):
        raise ConflictError(f"Category slug '{slug}' already exists.")
    category = Category(**data.model_dump(exclude={"slug"}), slug=slug)
    db.add(category)
    db.commit()
    return category


def update_category(db: Session, category_id: uuid.UUID, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    changes = data.model_dump(exclude_unset=True)
    if "slug" in changes and repo.slug_taken(db, changes["slug"], exclude_id=category.id):
        raise ConflictError(f"Category slug '{changes['slug']}' already exists.")
    for field, value in changes.items():
        setattr(category, field, value)
    db.commit()
    return category


def delete_category(db: Session, category_id: uuid.UUID) -> None:
    category = get_category(db, category_id)
    count = repo.product_count(db, category.id)
    if count:
        raise ConflictError(
            f"Category has {count} product(s). Move them or deactivate the category instead."
        )
    db.delete(category)
    db.commit()
