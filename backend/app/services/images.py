import io
import uuid
from typing import Final

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import BusinessRuleError, NotFoundError
from app.integrations.storage import get_storage
from app.models import ProductImage
from app.repositories import images as repo
from app.schemas.product import ImageUpdate
from app.services import products as product_service

ALLOWED_FORMATS: Final = {"JPEG", "PNG", "WEBP"}  # no SVG for product photos (scriptable)
MAX_PIXELS: Final = 50_000_000
MAX_IMAGES_PER_PRODUCT: Final = 10
# longest side in px; originals are never upscaled. "detail" keeps Full HD sources sharp.
SIZES: Final = {"detail": 1920, "card": 600, "thumb": 200}


def process_image(data: bytes) -> dict[str, bytes]:
    """Validate by actually decoding (never trust the filename or Content-Type) and make WebP sizes."""
    try:
        img = Image.open(io.BytesIO(data))
        if img.format not in ALLOWED_FORMATS:
            raise BusinessRuleError("Only JPEG, PNG or WebP images are allowed.")
        if img.width * img.height > MAX_PIXELS:
            raise BusinessRuleError("Image dimensions are too large.")
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise BusinessRuleError("File is not a valid image.") from exc

    img = ImageOps.exif_transpose(img)  # also drops the metadata (e.g. GPS) on re-encode
    img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    out: dict[str, bytes] = {}
    for name, longest in SIZES.items():
        variant = img.copy()
        variant.thumbnail((longest, longest), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        variant.save(buf, "WEBP", quality=85, method=4)
        out[name] = buf.getvalue()
    return out


def _paths(image: ProductImage) -> list[str]:
    return [f"{image.storage_path}/{name}.webp" for name in SIZES] if image.storage_path else []


def get_image(db: Session, image_id: uuid.UUID) -> ProductImage:
    image = repo.get(db, image_id)
    if image is None:
        raise NotFoundError("Image not found.")
    return image


def add_image(
    db: Session, product_id: uuid.UUID, data: bytes, alt_text: str | None
) -> ProductImage:
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    if not data:
        raise BusinessRuleError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise BusinessRuleError(f"Image is larger than {get_settings().max_upload_mb} MB.")
    product_service.get_product(db, product_id)  # 404 if missing
    existing = repo.count_for_product(db, product_id)
    if existing >= MAX_IMAGES_PER_PRODUCT:
        raise BusinessRuleError(f"A product can have at most {MAX_IMAGES_PER_PRODUCT} images.")

    variants = process_image(data)
    image_id = uuid.uuid4()
    prefix = f"products/{product_id}/{image_id}"
    storage = get_storage()
    urls = {
        name: storage.save(f"{prefix}/{name}.webp", blob, "image/webp")
        for name, blob in variants.items()
    }

    image = ProductImage(
        id=image_id,
        product_id=product_id,
        url=urls["detail"],
        storage_path=prefix,
        alt_text=alt_text,
        sort_order=existing,
        is_primary=existing == 0,
    )
    try:
        db.add(image)
        db.commit()
    except Exception:
        db.rollback()
        storage.delete([f"{prefix}/{name}.webp" for name in SIZES])  # don't leave orphaned files
        raise
    return image


def update_image(db: Session, image_id: uuid.UUID, data: ImageUpdate) -> ProductImage:
    image = get_image(db, image_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("is_primary") is True and not image.is_primary:
        repo.clear_primary(db, image.product_id)
    if changes.get("is_primary") is False and image.is_primary:
        raise BusinessRuleError("Choose another image as primary instead of unsetting this one.")
    for field, value in changes.items():
        setattr(image, field, value)
    db.commit()
    return image


def reorder(db: Session, product_id: uuid.UUID, ids: list[uuid.UUID]) -> list[ProductImage]:
    product_service.get_product(db, product_id)
    images = repo.list_for_product(db, product_id)
    if sorted(ids, key=str) != sorted((i.id for i in images), key=str):
        raise BusinessRuleError("Provide every image id of this product exactly once.")
    position = {image_id: n for n, image_id in enumerate(ids)}
    for image in images:
        image.sort_order = position[image.id]
    db.commit()
    return sorted(images, key=lambda i: i.sort_order)


def delete_image(db: Session, image_id: uuid.UUID) -> None:
    image = get_image(db, image_id)
    paths, product_id, was_primary = _paths(image), image.product_id, image.is_primary
    db.delete(image)
    db.flush()
    if was_primary:  # promote the next image so the product keeps a primary
        remaining = repo.list_for_product(db, product_id)
        if remaining:
            remaining[0].is_primary = True
    db.commit()
    get_storage().delete(paths)
