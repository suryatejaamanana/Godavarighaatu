from typing import Annotated

from fastapi import APIRouter, Query

from app.core.db import DB
from app.repositories.products import ProductSort
from app.schemas.common import Page
from app.schemas.product import ProductPublic
from app.services import products as service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=Page[ProductPublic])
def list_products(
    db: DB,
    q: Annotated[str | None, Query(max_length=100)] = None,
    category: Annotated[str | None, Query(description="Category slug")] = None,
    featured: bool = False,
    best_seller: bool = False,
    new_arrival: bool = False,
    sort: ProductSort = ProductSort.NEWEST,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=60)] = 12,
):
    products, total = service.list_public(
        db,
        q=q,
        category_slug=category,
        flags={
            "is_featured": featured,
            "is_best_seller": best_seller,
            "is_new_arrival": new_arrival,
        },
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return Page(
        items=[ProductPublic.from_product(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{slug}", response_model=ProductPublic)
def get_product(slug: str, db: DB):
    return ProductPublic.from_product(service.get_public_by_slug(db, slug))


@router.get("/{slug}/related", response_model=list[ProductPublic])
def related_products(slug: str, db: DB):
    product = service.get_public_by_slug(db, slug)
    return [ProductPublic.from_product(p) for p in service.get_related(db, product)]
