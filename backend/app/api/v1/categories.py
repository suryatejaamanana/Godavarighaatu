from fastapi import APIRouter

from app.core.db import DB
from app.schemas.category import CategoryOut
from app.services import categories as service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: DB):
    return service.list_categories(db, active_only=True)
