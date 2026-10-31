import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import require_admin
from app.core.db import DB
from app.models.enums import ProductStatus
from app.repositories.products import ProductSort
from app.schemas.common import Page
from app.schemas.product import (
    InventoryAdjust,
    InventorySet,
    LowStockItem,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    VariantCreate,
    VariantOut,
    VariantUpdate,
)
from app.services import products as service

router = APIRouter(tags=["admin: products"], dependencies=[Depends(require_admin)])


# ---------- products ----------
@router.get("/products", response_model=Page[ProductOut])
def list_products(
    db: DB,
    q: Annotated[str | None, Query(max_length=100)] = None,
    category_id: uuid.UUID | None = None,
    status_: Annotated[ProductStatus | None, Query(alias="status")] = None,
    sort: ProductSort = ProductSort.NEWEST,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    products, total = service.list_admin(
        db, q=q, category_id=category_id, status=status_, sort=sort, page=page, page_size=page_size
    )
    return Page(
        items=[ProductOut.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: DB):
    return service.create_product(db, data)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: uuid.UUID, db: DB):
    return service.get_product(db, product_id)


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: uuid.UUID, data: ProductUpdate, db: DB):
    return service.update_product(db, product_id, data)


@router.post("/products/{product_id}/archive", response_model=ProductOut)
def archive_product(product_id: uuid.UUID, db: DB):
    return service.set_status(db, product_id, ProductStatus.ARCHIVED)


@router.post("/products/{product_id}/restore", response_model=ProductOut)
def restore_product(product_id: uuid.UUID, db: DB):
    """Un-archive into 'inactive'; activate explicitly via PATCH when ready to sell."""
    return service.set_status(db, product_id, ProductStatus.INACTIVE)


# ---------- variants ----------
@router.get("/products/{product_id}/variants", response_model=list[VariantOut])
def list_variants(product_id: uuid.UUID, db: DB):
    return service.list_variants(db, product_id)


@router.post(
    "/products/{product_id}/variants",
    response_model=VariantOut,
    status_code=status.HTTP_201_CREATED,
)
def create_variant(product_id: uuid.UUID, data: VariantCreate, db: DB):
    return service.create_variant(db, product_id, data)


@router.get("/variants/{variant_id}", response_model=VariantOut)
def get_variant(variant_id: uuid.UUID, db: DB):
    return service.get_variant(db, variant_id)


@router.patch("/variants/{variant_id}", response_model=VariantOut)
def update_variant(variant_id: uuid.UUID, data: VariantUpdate, db: DB):
    return service.update_variant(db, variant_id, data)


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(variant_id: uuid.UUID, db: DB):
    service.delete_variant(db, variant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- inventory ----------
@router.get("/inventory/low-stock", response_model=list[LowStockItem])
def low_stock(db: DB):
    return service.low_stock(db)


@router.put("/variants/{variant_id}/inventory", response_model=VariantOut)
def set_inventory(variant_id: uuid.UUID, data: InventorySet, db: DB):
    return service.set_inventory(db, variant_id, data)


@router.post("/variants/{variant_id}/inventory/adjustments", response_model=VariantOut)
def adjust_inventory(variant_id: uuid.UUID, data: InventoryAdjust, db: DB):
    return service.adjust_inventory(db, variant_id, data)
