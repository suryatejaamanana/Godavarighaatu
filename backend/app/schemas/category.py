import uuid
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PatchModel, Slug


class CategoryCreate(BaseModel):
    slug: Slug | None = None  # generated from the name when omitted
    name: str = Field(min_length=1, max_length=120)
    name_te: str | None = Field(default=None, max_length=120)
    description: str | None = None
    description_te: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(PatchModel):
    non_nullable: ClassVar[set[str]] = {"slug", "name", "sort_order", "is_active"}

    slug: Slug | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    name_te: str | None = Field(default=None, max_length=120)
    description: str | None = None
    description_te: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    name_te: str | None
    description: str | None
    description_te: str | None
    image_url: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
