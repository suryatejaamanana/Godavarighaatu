"""Development only: fill an EMPTY database with clearly marked SAMPLE categories and products.

    DATABASE_URL=... JWT_SECRET=... uv run python -m scripts.seed_dev_catalog

All names start with "Sample", prices and stock are made-up placeholders, and some products
deliberately have no photo (to see the placeholder). Real products are added in the admin panel.
Refuses to run outside APP_ENV=development or on a database that already has categories.
"""

import io
import sys
from decimal import Decimal

from PIL import Image, ImageDraw

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models import Category
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate, VariantCreate
from app.services import categories as category_service
from app.services import images as image_service
from app.services import products as product_service

if not get_settings().is_development:
    sys.exit("Refusing to seed sample data outside APP_ENV=development.")

CATEGORIES = [
    ("Veg Pickles", "శాఖాహార పచ్చళ్ళు"),
    ("Non-Veg Pickles", "మాంసాహార పచ్చళ్ళు"),
    ("Gongura Pickles", "గోంగూర పచ్చళ్ళు"),
    ("Mango Pickles", "మామిడి పచ్చళ్ళు"),
    ("Chicken Pickles", "చికెన్ పచ్చళ్ళు"),
    ("Mutton Pickles", "మటన్ పచ్చళ్ళు"),
    ("Prawn Pickles", "రొయ్యల పచ్చళ్ళు"),
    ("Fish Pickles", "చేపల పచ్చళ్ళు"),
    ("Special Pickles", "స్పెషల్ పచ్చళ్ళు"),
]

# (name, telugu, category, flags, has_photo, in_stock)
PRODUCTS = [
    (
        "Boneless Gongura Chicken Pickle",
        "బోన్‌లెస్ గోంగూర చికెన్ పచ్చడి",
        "Chicken Pickles",
        {"is_featured": True, "is_best_seller": True},
        True,
        True,
    ),
    ("Gongura Pickle", "గోంగూర పచ్చడి", "Gongura Pickles", {"is_best_seller": True}, True, True),
    (
        "Mango Avakaya",
        "మామిడి ఆవకాయ",
        "Mango Pickles",
        {"is_new_arrival": True, "is_best_seller": True},
        True,
        True,
    ),
    ("Mutton Pickle", "మటన్ పచ్చడి", "Mutton Pickles", {"is_featured": True}, False, True),
    ("Prawn Pickle", "రొయ్యల పచ్చడి", "Prawn Pickles", {}, True, False),
    ("Fish Pickle", "చేపల పచ్చడి", "Fish Pickles", {"is_new_arrival": True}, False, True),
    ("Tomato Pickle", "టమాటా పచ్చడి", "Veg Pickles", {}, True, True),
    ("Lemon Pickle", "నిమ్మకాయ పచ్చడి", "Veg Pickles", {"is_new_arrival": True}, False, True),
    ("Chicken Pickle", "చికెన్ పచ్చడి", "Chicken Pickles", {"is_best_seller": True}, True, True),
    (
        "Special Mixed Pickle",
        "స్పెషల్ మిక్స్డ్ పచ్చడి",
        "Special Pickles",
        {"is_featured": True},
        False,
        True,
    ),
    ("Ginger Pickle", "అల్లం పచ్చడి", "Veg Pickles", {}, False, True),
    ("Garlic Pickle", "వెల్లుల్లి పచ్చడి", "Veg Pickles", {}, False, True),
    ("Gongura Mutton Pickle", "గోంగూర మటన్ పచ్చడి", "Non-Veg Pickles", {}, False, True),
    ("Gongura Prawn Pickle", "గోంగూర రొయ్యల పచ్చడి", "Non-Veg Pickles", {}, False, True),
    ("Magaya Mango Pickle", "మాగాయ", "Mango Pickles", {}, False, True),
]
PRICES = {"250g": Decimal(150), "500g": Decimal(290), "1kg": Decimal(560)}  # placeholders


def fake_photo(label: str, hue: int) -> bytes:
    """A generated 1600x1200 placeholder photo so uploads, sizes and layout can be tested."""
    img = Image.new("RGB", (1600, 1200), (165 + hue % 60, 31 + hue % 50, 24))
    draw = ImageDraw.Draw(img)
    draw.ellipse((400, 250, 1200, 1050), fill=(255, 201, 40))
    draw.ellipse((470, 320, 1130, 980), fill=(53, 37, 30))
    draw.text((60, 60), f"SAMPLE PHOTO: {label}", fill=(255, 248, 237))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue()


with get_session_factory()() as db:
    if db.query(Category).count():
        sys.exit("Database already has categories; refusing to add sample data.")
    by_name = {}
    for order, (name, name_te) in enumerate(CATEGORIES):
        by_name[name] = category_service.create_category(
            db, CategoryCreate(name=name, name_te=name_te, sort_order=order)
        )
    for n, (name, name_te, category, flags, has_photo, in_stock) in enumerate(PRODUCTS):
        variants = [
            VariantCreate(
                weight=w,
                price=price,
                compare_at_price=price + Decimal(30) if w == "500g" and n % 2 == 0 else None,
                quantity=(40 if in_stock else 0) if w != "1kg" else (3 if in_stock else 0),
            )
            for w, price in PRICES.items()
        ]
        product = product_service.create_product(
            db,
            ProductCreate(
                name=f"Sample {name}",
                name_te=name_te,
                category_id=by_name[category].id,
                short_description="Sample product for development. Not a real listing.",
                description="This is placeholder text for a development sample product.",
                ingredients="Sample ingredients (placeholder).",
                shelf_life="Placeholder",
                variants=variants,
                **flags,
            ),
        )
        if has_photo:
            for shot in range(2 if n == 0 else 1):
                image_service.add_image(db, product.id, fake_photo(name, n * 37 + shot * 90), name)
    print(f"Seeded {len(CATEGORIES)} categories and {len(PRODUCTS)} sample products.")
