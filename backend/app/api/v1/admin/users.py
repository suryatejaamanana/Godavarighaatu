import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentAdmin, require_super_admin
from app.core.db import DB
from app.schemas.auth import AdminCreate, AdminOut, AdminUpdate
from app.services import admins as service

router = APIRouter(
    prefix="/users", tags=["admin: users"], dependencies=[Depends(require_super_admin)]
)


@router.get("", response_model=list[AdminOut])
def list_admins(db: DB):
    return service.list_admins(db)


@router.post("", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def create_admin(data: AdminCreate, db: DB):
    return service.create_admin(db, data)


@router.patch("/{admin_id}", response_model=AdminOut)
def update_admin(admin_id: uuid.UUID, data: AdminUpdate, actor: CurrentAdmin, db: DB):
    return service.update_admin(db, actor, admin_id, data)
