import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.api.deps import require_manager, require_staff
from app.core.config import get_settings
from app.core.db import DB
from app.schemas.product import DashboardSummary, ImageOrder, ImageUpdate, ProductImageOut
from app.services import images as service
from app.services import products as product_service

router = APIRouter(tags=["admin: images"], dependencies=[Depends(require_manager)])
dashboard_router = APIRouter(tags=["admin: dashboard"], dependencies=[Depends(require_staff)])


@router.post(
    "/products/{product_id}/images",
    response_model=ProductImageOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_image(
    product_id: uuid.UUID,
    db: DB,
    file: Annotated[UploadFile, File()],
    alt_text: Annotated[str | None, Form(max_length=200)] = None,
):
    # Read one byte past the limit so oversized uploads are detected without loading them fully.
    data = file.file.read(get_settings().max_upload_mb * 1024 * 1024 + 1)
    return service.add_image(db, product_id, data, alt_text)


@router.put("/products/{product_id}/images/order", response_model=list[ProductImageOut])
def reorder_images(product_id: uuid.UUID, data: ImageOrder, db: DB):
    return service.reorder(db, product_id, data.ids)


@router.patch("/images/{image_id}", response_model=ProductImageOut)
def update_image(image_id: uuid.UUID, data: ImageUpdate, db: DB):
    return service.update_image(db, image_id, data)


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: uuid.UUID, db: DB):
    service.delete_image(db, image_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@dashboard_router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: DB):
    return product_service.dashboard_summary(db)
