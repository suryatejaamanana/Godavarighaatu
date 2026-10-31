import uuid
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.models.enums import AdminRole
from app.schemas.common import PatchModel

Password = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    role: AdminRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class AdminCreate(BaseModel):
    email: EmailStr
    password: str = Password
    full_name: str | None = Field(default=None, max_length=120)
    role: AdminRole = AdminRole.STAFF

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class AdminUpdate(PatchModel):
    non_nullable: ClassVar[set[str]] = {"role", "is_active", "password"}

    full_name: str | None = Field(default=None, max_length=120)
    role: AdminRole | None = None
    is_active: bool | None = None
    password: str | None = Field(
        default=None, min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH
    )
