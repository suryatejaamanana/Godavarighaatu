import uuid

import pytest

from app.core.config import get_settings

A = "/api/v1/admin"
P = "/api/v1"


@pytest.fixture
def category(client):
    r = client.post(f"{A}/categories", json={"name": "Non-Veg Pickles", "name_te": "నాన్ వెజ్"})
    assert r.status_code == 201
    return r.json()


def make_product(client, category, name="Gongura Chicken Pickle", **extra):
    body = {"name": name, "category_id": category["id"], **extra}
    r = client.post(f"{A}/products", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def variant(weight="500g", price="350.00", **extra):
    return {"weight": weight, "price": price, **extra}


# ---------------- admin gate ----------------
def test_admin_api_refused_outside_development(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "production")
    assert client.get(f"{A}/categories").status_code == 503
    assert client.get(f"{P}/categories").status_code == 200  # public API unaffected


# ---------------- categories ----------------
def test_category_crud(client, category):
    assert category["slug"] == "non-veg-pickles" and category["is_active"] is True
    cid = category["id"]
    r = client.patch(f"{A}/categories/{cid}", json={"name_te": None, "sort_order": 3})
    assert r.status_code == 200 and r.json()["name_te"] is None and r.json()["sort_order"] == 3
    assert client.get(f"{A}/categories/{cid}").json()["name"] == "Non-Veg Pickles"
    assert client.delete(f"{A}/categories/{cid}").status_code == 204
    assert client.get(f"{A}/categories/{cid}").status_code == 404


def test_category_validation_and_conflicts(client, category):
    assert client.post(f"{A}/categories", json={"name": ""}).status_code == 422
    assert client.post(f"{A}/categories", json={"name": "X", "slug": "Bad Slug"}).status_code == 422
    assert client.post(f"{A}/categories", json={"name": "Non-Veg Pickles"}).status_code == 409
    r = client.patch(f"{A}/categories/{category['id']}", json={"name": None})
    assert r.status_code == 422  # name cannot be nulled
    assert client.get(f"{A}/categories/{uuid.uuid4()}").status_code == 404
    assert client.get(f"{A}/categories/not-a-uuid").status_code == 422


def test_category_with_products_cannot_be_deleted(client, category):
    make_product(client, category)
    assert client.delete(f"{A}/categories/{category['id']}").status_code == 409


def test_public_categories_hide_inactive(client, category):
    client.post(f"{A}/categories", json={"name": "Hidden", "is_active": False})
    slugs = [c["slug"] for c in client.get(f"{P}/categories").json()]
    assert slugs == ["non-veg-pickles"]
    assert len(client.get(f"{A}/categories").json()) == 2


# ---------------- products ----------------
def test_create_product_with_variants_and_stock(client, category):
    p = make_product(
        client,
        category,
        variants=[
            variant("250g", "200.00", quantity=5),
            variant("1kg", "650.00", compare_at_price="700.00", quantity=2, sku="GCP-1KG"),
        ],
        badges=["Bestseller"],
    )
    assert p["slug"] == "gongura-chicken-pickle" and p["status"] == "active"
    by_weight = {v["weight"]: v for v in p["variants"]}
    assert by_weight["250g"]["inventory"] == {
        "quantity": 5, "reserved": 0, "low_stock_threshold": 5, "available": 5,
    }  # fmt: skip
    assert by_weight["1kg"]["discount_percent"] == 7  # (700-650)/700
    assert p["sold_count"] == 0 and p["images"] == []


def test_product_validation(client, category):
    cid = category["id"]
    bad = [
        {"name": "x", "category_id": str(uuid.uuid4())},  # unknown category -> 422 (business rule)
        {"name": "", "category_id": cid},
        {"name": "x", "category_id": cid, "variants": [variant("2kg")]},
        {"name": "x", "category_id": cid, "variants": [variant(price="-1")]},
        {"name": "x", "category_id": cid, "variants": [variant(price="1.234")]},
        {"name": "x", "category_id": cid, "variants": [variant(price="10", compare_at_price="5")]},
        {"name": "x", "category_id": cid, "variants": [variant("250g"), variant("250g")]},
        {"name": "x", "category_id": cid, "badges": [""]},
        {"name": "Telugu only తెలుగు", "slug": "NOT OK", "category_id": cid},
    ]
    for body in bad:
        assert client.post(f"{A}/products", json=body).status_code == 422, body


def test_product_slug_and_sku_conflicts(client, category):
    make_product(client, category, variants=[variant(sku="DUP")])
    r = client.post(
        f"{A}/products", json={"name": "Gongura Chicken Pickle", "category_id": category["id"]}
    )
    assert r.status_code == 409
    r = client.post(
        f"{A}/products",
        json={"name": "Other", "category_id": category["id"], "variants": [variant(sku="DUP")]},
    )
    assert r.status_code == 409


def test_update_archive_restore(client, category):
    p = make_product(client, category)
    pid = p["id"]
    r = client.patch(f"{A}/products/{pid}", json={"is_featured": True, "name_te": "గోంగూర చికెన్"})
    assert r.json()["is_featured"] is True and r.json()["name_te"] == "గోంగూర చికెన్"
    assert client.patch(f"{A}/products/{pid}", json={"status": None}).status_code == 422
    assert client.patch(f"{A}/products/{pid}", json={"status": "bogus"}).status_code == 422
    assert (
        client.patch(f"{A}/products/{pid}", json={"category_id": str(uuid.uuid4())}).status_code
        == 422
    )
    assert client.post(f"{A}/products/{pid}/archive").json()["status"] == "archived"
    assert client.get(f"{P}/products/{p['slug']}").status_code == 404  # hidden from storefront
    assert client.post(f"{A}/products/{pid}/restore").json()["status"] == "inactive"
    assert client.get(f"{A}/products/{uuid.uuid4()}").status_code == 404


def test_admin_product_list_filters(client, category):
    make_product(client, category, "Alpha Pickle")
    b = make_product(client, category, "Beta Pickle")
    client.post(f"{A}/products/{b['id']}/archive")
    assert client.get(f"{A}/products").json()["total"] == 2
    r = client.get(f"{A}/products", params={"status": "archived"}).json()
    assert [x["name"] for x in r["items"]] == ["Beta Pickle"]
    assert client.get(f"{A}/products", params={"q": "alph"}).json()["total"] == 1
    assert client.get(f"{A}/products", params={"page_size": 1000}).status_code == 422


# ---------------- variants ----------------
def test_variant_lifecycle(client, category):
    p = make_product(client, category)
    r = client.post(f"{A}/products/{p['id']}/variants", json=variant("250g", "200", quantity=3))
    assert r.status_code == 201
    v = r.json()
    assert v["inventory"]["available"] == 3
    # one variant per weight
    assert (
        client.post(f"{A}/products/{p['id']}/variants", json=variant("250g", "1")).status_code
        == 409
    )
    # independent prices per weight
    client.post(f"{A}/products/{p['id']}/variants", json=variant("500g", "380"))
    prices = {
        x["weight"]: x["price"] for x in client.get(f"{A}/products/{p['id']}/variants").json()
    }
    assert prices == {"250g": "200.00", "500g": "380.00"}
    # update: price, compare-at rules, weight immutable
    r = client.patch(f"{A}/variants/{v['id']}", json={"price": "210", "compare_at_price": "250"})
    assert r.status_code == 200 and r.json()["discount_percent"] == 16
    assert (
        client.patch(f"{A}/variants/{v['id']}", json={"price": "300"}).status_code == 422
    )  # > compare-at
    assert (
        client.patch(
            f"{A}/variants/{v['id']}", json={"compare_at_price": None, "price": "300"}
        ).status_code
        == 200
    )
    assert client.patch(f"{A}/variants/{v['id']}", json={"price": None}).status_code == 422
    # delete
    assert client.delete(f"{A}/variants/{v['id']}").status_code == 204
    assert client.get(f"{A}/variants/{v['id']}").status_code == 404
    assert client.post(f"{A}/products/{uuid.uuid4()}/variants", json=variant()).status_code == 404


# ---------------- inventory ----------------
def test_inventory_set_adjust_and_low_stock(client, category):
    p = make_product(client, category, variants=[variant("500g", "350", quantity=10)])
    vid = p["variants"][0]["id"]
    inv = f"{A}/variants/{vid}/inventory"

    r = client.put(inv, json={"quantity": 20, "low_stock_threshold": 3})
    assert (
        r.json()["inventory"]["quantity"] == 20
        and r.json()["inventory"]["low_stock_threshold"] == 3
    )
    assert client.put(inv, json={"quantity": -1}).status_code == 422

    assert (
        client.post(f"{inv}/adjustments", json={"delta": -5}).json()["inventory"]["quantity"] == 15
    )
    assert client.post(f"{inv}/adjustments", json={"delta": 0}).status_code == 422
    assert (
        client.post(f"{inv}/adjustments", json={"delta": -16}).status_code == 422
    )  # negative stock

    assert client.get(f"{A}/inventory/low-stock").json() == []
    client.put(inv, json={"quantity": 2})
    low = client.get(f"{A}/inventory/low-stock").json()
    assert [(i["product_name"], i["available"]) for i in low] == [("Gongura Chicken Pickle", 2)]
    assert (
        client.put(f"{A}/variants/{uuid.uuid4()}/inventory", json={"quantity": 1}).status_code
        == 404
    )


def test_inventory_cannot_drop_below_reserved(client, category, db):
    from app.models import Inventory

    p = make_product(client, category, variants=[variant(quantity=10)])
    vid = p["variants"][0]["id"]
    db.query(Inventory).filter(Inventory.variant_id == uuid.UUID(vid)).update({"reserved": 4})
    assert client.put(f"{A}/variants/{vid}/inventory", json={"quantity": 3}).status_code == 422
    assert (
        client.post(f"{A}/variants/{vid}/inventory/adjustments", json={"delta": -7}).status_code
        == 422
    )
    r = client.put(f"{A}/variants/{vid}/inventory", json={"quantity": 4})
    assert r.status_code == 200 and r.json()["inventory"]["available"] == 0


# ---------------- storefront ----------------
def test_storefront_listing_search_filter_sort_pagination(client, category):
    veg = client.post(f"{A}/categories", json={"name": "Veg Pickles"}).json()
    a = make_product(
        client, category, "Chicken Pickle", variants=[variant("250g", "400", quantity=1)]
    )
    make_product(client, veg, "Mango Pickle", variants=[variant("250g", "150", quantity=1)])
    make_product(client, veg, "Lemon Pickle", variants=[variant("250g", "100", quantity=1)])
    make_product(client, veg, "No Variants Pickle")
    hidden = make_product(client, veg, "Hidden Pickle", status="inactive")
    assert hidden["status"] == "inactive"

    names = lambda r: [i["name"] for i in r.json()["items"]]
    r = client.get(f"{P}/products", params={"sort": "price_asc"})
    assert names(r) == ["Lemon Pickle", "Mango Pickle", "Chicken Pickle", "No Variants Pickle"]
    assert r.json()["total"] == 4  # inactive hidden
    assert names(client.get(f"{P}/products", params={"sort": "price_desc"}))[:3] == [
        "Chicken Pickle", "Mango Pickle", "Lemon Pickle",
    ]  # fmt: skip
    assert (
        names(client.get(f"{P}/products", params={"category": "veg-pickles", "sort": "price_asc"}))[
            0
        ]
        == "Lemon Pickle"
    )
    assert names(client.get(f"{P}/products", params={"q": "mango"})) == ["Mango Pickle"]
    assert (
        client.get(f"{P}/products", params={"q": "100%"}).json()["total"] == 0
    )  # wildcard is escaped

    client.patch(f"{A}/products/{a['id']}", json={"is_best_seller": True})
    page1 = client.get(
        f"{P}/products", params={"page_size": 3, "page": 1, "sort": "price_asc"}
    ).json()
    page2 = client.get(
        f"{P}/products", params={"page_size": 3, "page": 2, "sort": "price_asc"}
    ).json()
    assert (len(page1["items"]), len(page2["items"]), page1["total"]) == (3, 1, 4)
    assert client.get(f"{P}/products", params={"page": 0}).status_code == 422


def test_popularity_sort(client, category, db):
    from app.models import Product

    make_product(client, category, "Slow")
    fast = make_product(client, category, "Fast")
    db.query(Product).filter(Product.id == uuid.UUID(fast["id"])).update({"sold_count": 50})
    r = client.get(f"{P}/products", params={"sort": "popular"}).json()
    assert [i["name"] for i in r["items"]] == ["Fast", "Slow"]


def test_storefront_product_detail_hides_internal_data(client, category):
    p = make_product(
        client,
        category,
        ingredients="Gongura, chicken, chilli",
        variants=[
            variant("250g", "200", quantity=0),
            variant("500g", "380", compare_at_price="400", quantity=7),
            variant("1kg", "700", is_active=False, quantity=9),
        ],
    )
    r = client.get(f"{P}/products/{p['slug']}")
    assert r.status_code == 200
    body = r.json()
    assert body["ingredients"] == "Gongura, chicken, chilli"
    assert [v["weight"] for v in body["variants"]] == [
        "250g",
        "500g",
    ]  # inactive hidden, price-sorted
    assert [v["in_stock"] for v in body["variants"]] == [False, True]
    assert body["in_stock"] is True and body["min_price"] == "200.00"
    assert body["max_discount_percent"] == 5
    assert "reserved" not in str(body) and "sold_count" not in body and "status" not in body
    assert client.get(f"{P}/products/nope").status_code == 404


def test_all_variants_out_of_stock_means_product_out_of_stock(client, category):
    p = make_product(client, category, variants=[variant(quantity=0)])
    assert client.get(f"{P}/products/{p['slug']}").json()["in_stock"] is False


def test_related_products_same_category_only(client, category):
    other = client.post(f"{A}/categories", json={"name": "Veg"}).json()
    a = make_product(client, category, "A Pickle")
    make_product(client, category, "B Pickle")
    make_product(client, category, "Inactive Pickle", status="inactive")
    make_product(client, other, "C Pickle")
    r = client.get(f"{P}/products/{a['slug']}/related").json()
    assert [x["name"] for x in r] == ["B Pickle"]


def test_inactive_category_hides_products_from_storefront(client, category):
    p = make_product(client, category)
    client.patch(f"{A}/categories/{category['id']}", json={"is_active": False})
    assert client.get(f"{P}/products").json()["total"] == 0
    assert client.get(f"{P}/products/{p['slug']}").status_code == 404
