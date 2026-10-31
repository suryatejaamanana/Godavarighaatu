import re
from decimal import Decimal
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, model_validator

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
Slug = Annotated[str, Field(min_length=1, max_length=160, pattern=SLUG_PATTERN)]
MoneyIn = Annotated[Decimal, Field(max_digits=10, decimal_places=2, ge=0)]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class PatchModel(BaseModel):
    """PATCH body: omitted fields are unchanged; fields in `non_nullable` may not be set to null."""

    non_nullable: ClassVar[set[str]] = set()

    @model_validator(mode="after")
    def _no_nulls(self):
        bad = [f for f in self.model_fields_set & self.non_nullable if getattr(self, f) is None]
        if bad:
            raise ValueError(f"{', '.join(sorted(bad))} cannot be null")
        return self
