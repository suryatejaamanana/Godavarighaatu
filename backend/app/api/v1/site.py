from fastapi import APIRouter
from sqlalchemy import select

from app.core.db import DB
from app.models import WebsiteSetting

router = APIRouter(tags=["site"])

# Only these keys are ever exposed publicly. Phase 11 adds the admin screen that edits them;
# until a key is set the storefront falls back to its built-in defaults.
PUBLIC_KEYS = frozenset(
    {
        "brand_name",
        "brand_name_te",
        "brand_tagline",
        "brand_label",
        "announcement",
        "announcement_te",
        "hero_headline",
        "hero_headline_te",
        "about_text",
        "about_text_te",
    }
)


@router.get("/site-settings")
def public_settings(db: DB) -> dict[str, str | int | bool | list | dict | None]:
    rows = db.execute(
        select(WebsiteSetting.key, WebsiteSetting.value).where(WebsiteSetting.key.in_(PUBLIC_KEYS))
    )
    return {key: value for key, value in rows}
