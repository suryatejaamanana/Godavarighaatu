import io
import uuid
from pathlib import Path

import httpx
import pytest
from PIL import Image

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError
from app.integrations.storage import LocalStorage, SupabaseStorage
from app.models.enums import AdminRole

A = "/api/v1/admin"


def make_image(fmt="JPEG", size=(800, 600), color=(200, 30, 20)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, fmt)
    return buf.getvalue()


@pytest.fixture
def media(tmp_path, monkeypatch) -> Path:
    storage = LocalStorage(tmp_path, "http://test/media")
    monkeypatch.setattr("app.services.images.get_storage", lambda: storage)
    return tmp_path


@pytest.fixture
def client(login_as):
    return login_as(AdminRole.MANAGER)[0]


@pytest.fixture
def product(client):
    cat = client.post(f"{A}/categories", json={"name": "Veg"}).json()
    return client.post(
        f"{A}/products", json={"name": "Mango Pickle", "category_id": cat["id"]}
    ).json()


def upload(client, product, data=None, name="photo.jpg", ctype="image/jpeg", **form):
    return client.post(
        f"{A}/products/{product['id']}/images",
        files={"file": (name, data if data is not None else make_image(), ctype)},
        data=form,
    )


def test_upload_creates_resized_webp_files(client, product, media):
    r = upload(client, product, make_image(size=(3000, 2000)), alt_text="Mango pickle jar")
    assert r.status_code == 201, r.text
    img = r.json()
    assert (
        img["is_primary"] is True
        and img["alt_text"] == "Mango pickle jar"
        and img["sort_order"] == 0
    )
    assert img["url"].endswith("/detail.webp")
    assert img["card_url"].endswith("/card.webp") and img["thumb_url"].endswith("/thumb.webp")

    folder = media / "products" / product["id"] / img["id"]
    sizes = {}
    for name in ("detail", "card", "thumb"):
        with Image.open(folder / f"{name}.webp") as im:
            assert im.format == "WEBP"
            sizes[name] = im.size
    assert sizes["detail"] == (1920, 1280)  # Full HD cap, aspect ratio kept
    assert sizes["card"][0] == 600 and sizes["thumb"][0] == 200


def test_small_images_are_not_upscaled(client, product, media):
    img = upload(client, product, make_image(size=(100, 80))).json()
    with Image.open(media / "products" / product["id"] / img["id"] / "detail.webp") as im:
        assert im.size == (100, 80)


def test_png_with_transparency_and_webp_accepted(client, product, media):
    rgba = io.BytesIO()
    Image.new("RGBA", (50, 50), (255, 0, 0, 0)).save(rgba, "PNG")
    assert upload(client, product, rgba.getvalue(), "a.png", "image/png").status_code == 201
    assert upload(client, product, make_image("WEBP"), "b.webp", "image/webp").status_code == 201


def test_images_appear_on_product_and_storefront(client, product, media):
    upload(client, product)
    admin = client.get(f"{A}/products/{product['id']}").json()
    assert len(admin["images"]) == 1 and admin["images"][0]["thumb_url"]
    public = client.get(f"/api/v1/products/{product['slug']}").json()
    assert public["images"][0]["card_url"].endswith("card.webp")


@pytest.mark.parametrize(
    ("data", "name", "ctype"),
    [
        (b"not an image at all", "x.jpg", "image/jpeg"),  # wrong content, right name
        (b"", "x.jpg", "image/jpeg"),
        (
            b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            "x.svg",
            "image/svg+xml",
        ),
        (make_image("GIF"), "x.gif", "image/gif"),  # real image, format not allowed
        (make_image("BMP"), "x.jpg", "image/jpeg"),  # disguised as jpg
    ],
)
def test_invalid_uploads_rejected(client, product, media, data, name, ctype):
    assert upload(client, product, data, name, ctype).status_code == 422
    assert client.get(f"{A}/products/{product['id']}").json()["images"] == []
    assert not list(media.rglob("*.webp"))  # nothing stored


def test_oversized_and_overlimit_uploads_rejected(client, product, media, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    big = make_image(size=(1500, 1500), color=(1, 2, 3))
    noisy = io.BytesIO()
    Image.effect_noise((1200, 1200), 100).convert("RGB").save(noisy, "PNG")
    assert len(noisy.getvalue()) > 1024 * 1024
    assert upload(client, product, noisy.getvalue(), "n.png", "image/png").status_code == 422
    assert upload(client, product, big).status_code == 201  # small file size, fine


def test_max_ten_images_per_product(client, product, media):
    for _ in range(10):
        assert upload(client, product, make_image(size=(20, 20))).status_code == 201
    assert upload(client, product, make_image(size=(20, 20))).status_code == 422


def test_missing_product_and_missing_file(client, media):
    r = client.post(
        f"{A}/products/{uuid.uuid4()}/images", files={"file": ("a.jpg", make_image(), "image/jpeg")}
    )
    assert r.status_code == 404
    assert client.post(f"{A}/products/{uuid.uuid4()}/images").status_code == 422


def test_primary_switching_ordering_and_delete(client, product, media):
    a, b, c = (upload(client, product).json() for _ in range(3))
    assert [a["is_primary"], b["is_primary"], c["is_primary"]] == [True, False, False]

    r = client.patch(f"{A}/images/{c['id']}", json={"is_primary": True, "alt_text": "Third"})
    assert r.status_code == 200 and r.json()["is_primary"] is True
    images = client.get(f"{A}/products/{product['id']}").json()["images"]
    assert [i["is_primary"] for i in images] == [False, False, True]  # exactly one primary
    assert client.patch(f"{A}/images/{c['id']}", json={"is_primary": False}).status_code == 422
    assert client.patch(f"{A}/images/{c['id']}", json={"sort_order": None}).status_code == 422

    r = client.put(
        f"{A}/products/{product['id']}/images/order", json={"ids": [c["id"], a["id"], b["id"]]}
    )
    assert [i["id"] for i in r.json()] == [c["id"], a["id"], b["id"]]
    bad = client.put(f"{A}/products/{product['id']}/images/order", json={"ids": [a["id"]]})
    assert bad.status_code == 422

    folder = media / "products" / product["id"] / c["id"]
    assert folder.exists()
    assert client.delete(f"{A}/images/{c['id']}").status_code == 204
    assert not list(folder.glob("*.webp"))  # files removed from storage
    images = client.get(f"{A}/products/{product['id']}").json()["images"]
    assert [i["id"] for i in images] == [a["id"], b["id"]]
    assert images[0]["is_primary"] is True  # a new primary was promoted
    assert client.delete(f"{A}/images/{c['id']}").status_code == 404


def test_staff_cannot_upload_but_manager_can(login_as, product, media):
    staff, _ = login_as(AdminRole.STAFF)
    assert upload(staff, product).status_code == 403


def test_dashboard_summary(client, login_as):
    cat = client.post(f"{A}/categories", json={"name": "C"}).json()
    mk = lambda name, **kw: client.post(
        f"{A}/products",
        json={"name": name, "category_id": cat["id"], **kw},
    ).json()
    mk(
        "Live",
        variants=[
            {"weight": "250g", "price": "10", "quantity": 0},
            {"weight": "500g", "price": "20", "quantity": 50},
        ],
    )
    mk("Hidden", status="inactive")
    client.post(f"{A}/products/{mk('Old')['id']}/archive")
    staff, _ = login_as(AdminRole.STAFF)
    s = staff.get(f"{A}/dashboard/summary").json()
    assert s == {
        "products_total": 3, "products_active": 1, "products_inactive": 1, "products_archived": 1,
        "categories_total": 1, "variants_out_of_stock": 1, "variants_low_stock": 1,
    }  # fmt: skip


# ---------------- storage backends ----------------
def test_local_storage_blocks_path_traversal(tmp_path):
    storage = LocalStorage(tmp_path / "root", "http://x/media")
    assert storage.save("a/b.webp", b"1", "image/webp") == "http://x/media/a/b.webp"
    with pytest.raises(ValueError):
        storage.save("../escape.webp", b"1", "image/webp")
    storage.delete(["a/b.webp", "a/missing.webp"])  # missing files are fine
    assert not (tmp_path / "root" / "a" / "b.webp").exists()


def test_supabase_storage_requests():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(500 if "fail" in request.url.path else 200)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    storage = SupabaseStorage("https://proj.supabase.co/", "service-key", "product-images", client)
    url = storage.save("products/p/i/detail.webp", b"data", "image/webp")
    assert (
        url
        == "https://proj.supabase.co/storage/v1/object/public/product-images/products/p/i/detail.webp"
    )
    up = seen[0]
    assert (
        up.method == "POST"
        and up.url.path == "/storage/v1/object/product-images/products/p/i/detail.webp"
    )
    assert (
        up.headers["authorization"] == "Bearer service-key"
        and up.headers["content-type"] == "image/webp"
    )
    assert up.content == b"data"

    with pytest.raises(ServiceUnavailableError):
        storage.save("fail.webp", b"x", "image/webp")
    storage.delete(["a.webp"])
    assert seen[-1].method == "DELETE" and b"a.webp" in seen[-1].content
