import uuid

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import require_admin
from app.core.db import DB
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import categories as service

router = APIRouter(
    prefix="/categories", tags=["admin: categories"], dependencies=[Depends(require_admin)]
)


@router.get("", response_model=list[CategoryOut])
def list_categories(db: DB):
    return service.list_categories(db, active_only=False)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: DB):
    return service.create_category(db, data)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: uuid.UUID, db: DB):
    return service.get_category(db, category_id)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(category_id: uuid.UUID, data: CategoryUpdate, db: DB):
    return service.update_category(db, category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: uuid.UUID, db: DB):
    service.delete_category(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
