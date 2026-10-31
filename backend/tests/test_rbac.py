import uuid

import pytest

from app.main import app
from app.models.enums import AdminRole
from tests.conftest import PASSWORD

A = "/api/v1/admin"
ID = str(uuid.uuid4())

STAFF, MANAGER, SUPER = AdminRole.STAFF, AdminRole.MANAGER, AdminRole.SUPER_ADMIN

# (method, path, json body, minimum role). Allowed roles must get past authorization
# (any status except 401/403); lower roles must get 403.
MATRIX = [
    ("GET", f"{A}/categories", None, STAFF),
    ("GET", f"{A}/categories/{ID}", None, STAFF),
    ("POST", f"{A}/categories", {"name": "Z"}, MANAGER),
    ("PATCH", f"{A}/categories/{ID}", {"name": "Z"}, MANAGER),
    ("DELETE", f"{A}/categories/{ID}", None, MANAGER),
    ("GET", f"{A}/products", None, STAFF),
    ("GET", f"{A}/products/{ID}", None, STAFF),
    ("POST", f"{A}/products", {"name": "Z", "category_id": ID}, MANAGER),
    ("PATCH", f"{A}/products/{ID}", {"name": "Z"}, MANAGER),
    ("POST", f"{A}/products/{ID}/archive", None, MANAGER),
    ("POST", f"{A}/products/{ID}/restore", None, MANAGER),
    ("GET", f"{A}/products/{ID}/variants", None, STAFF),
    ("POST", f"{A}/products/{ID}/variants", {"weight": "250g", "price": "1"}, MANAGER),
    ("GET", f"{A}/variants/{ID}", None, STAFF),
    ("PATCH", f"{A}/variants/{ID}", {"price": "1"}, MANAGER),
    ("DELETE", f"{A}/variants/{ID}", None, MANAGER),
    ("GET", f"{A}/inventory/low-stock", None, STAFF),
    ("PUT", f"{A}/variants/{ID}/inventory", {"quantity": 1}, STAFF),
    ("POST", f"{A}/variants/{ID}/inventory/adjustments", {"delta": 1}, STAFF),
    ("GET", f"{A}/auth/me", None, STAFF),
    ("GET", f"{A}/users", None, SUPER),
    ("POST", f"{A}/users", {"email": "n@example.com", "password": PASSWORD}, SUPER),
    ("PATCH", f"{A}/users/{ID}", {"full_name": "Z"}, SUPER),
]
RANK = {STAFF: 1, MANAGER: 2, SUPER: 3}
PUBLIC_AUTH = {f"{A}/auth/login", f"{A}/auth/refresh", f"{A}/auth/logout"}


@pytest.mark.parametrize("role", list(AdminRole))
def test_role_permission_matrix(login_as, role):
    c, _ = login_as(role)
    for method, path, body, minimum in MATRIX:
        r = c.request(method, path, json=body)
        if RANK[role] >= RANK[minimum]:
            assert r.status_code not in (401, 403), (role, method, path, r.status_code)
        else:
            assert r.status_code == 403, (role, method, path, r.status_code)


def test_every_admin_route_requires_authentication(client):
    """Walks the real route table so a newly added admin route can't be forgotten."""
    checked = 0
    for path, methods in app.openapi()["paths"].items():
        if not path.startswith(f"{A}/") or path in PUBLIC_AUTH:
            continue
        concrete = path.replace("{category_id}", ID).replace("{product_id}", ID)
        concrete = concrete.replace("{variant_id}", ID).replace("{admin_id}", ID)
        for method in methods:
            r = client.request(method.upper(), concrete, json={})
            assert r.status_code == 401, (method, path, r.status_code)
            checked += 1
    assert checked >= 20


def test_matrix_covers_every_admin_route():
    documented = {(m, p) for m, p, *_ in MATRIX}
    for path, methods in app.openapi()["paths"].items():
        if not path.startswith(f"{A}/") or path in PUBLIC_AUTH:
            continue
        concrete = path
        for name in ("category_id", "product_id", "variant_id", "admin_id"):
            concrete = concrete.replace("{" + name + "}", ID)
        for method in methods:
            assert (method.upper(), concrete) in documented, (
                f"{method} {path} missing from RBAC matrix"
            )


def test_public_storefront_needs_no_login(client):
    assert client.get("/api/v1/categories").status_code == 200
    assert client.get("/api/v1/products").status_code == 200


# ---------------- admin user management (super_admin) ----------------
def test_super_admin_creates_admins_who_can_log_in(login_as, make_client):
    boss, _ = login_as(SUPER)
    r = boss.post(
        f"{A}/users", json={"email": "New@Example.com", "password": PASSWORD, "role": "manager"}
    )
    assert r.status_code == 201
    body = r.json()
    assert (
        body["email"] == "new@example.com"
        and body["role"] == "manager"
        and "password" not in str(body)
    )
    newcomer = make_client()
    assert (
        newcomer.post(
            f"{A}/auth/login", json={"email": "new@example.com", "password": PASSWORD}
        ).status_code
        == 200
    )
    assert {u["email"] for u in boss.get(f"{A}/users").json()} >= {"new@example.com"}


def test_admin_creation_validation(login_as):
    boss, admin = login_as(SUPER)
    ok = {"email": "x@example.com", "password": PASSWORD}
    assert boss.post(f"{A}/users", json={**ok, "password": "short"}).status_code == 422
    assert boss.post(f"{A}/users", json={**ok, "email": "bad"}).status_code == 422
    assert boss.post(f"{A}/users", json={**ok, "role": "owner"}).status_code == 422
    assert (
        boss.post(f"{A}/users", json={"email": admin.email, "password": PASSWORD}).status_code
        == 409
    )


def test_super_admin_cannot_change_own_role_or_status(login_as):
    boss, me = login_as(SUPER)
    assert boss.patch(f"{A}/users/{me.id}", json={"role": "staff"}).status_code == 422
    assert boss.patch(f"{A}/users/{me.id}", json={"is_active": False}).status_code == 422
    assert boss.patch(f"{A}/users/{me.id}", json={"full_name": "Boss"}).status_code == 200


def test_deactivating_or_resetting_password_ends_target_sessions(login_as, make_client):
    boss, _ = login_as(SUPER)
    worker, worker_admin = login_as(STAFF)
    assert worker.get(f"{A}/auth/me").status_code == 200

    assert (
        boss.patch(f"{A}/users/{worker_admin.id}", json={"role": "manager"}).json()["role"]
        == "manager"
    )
    assert boss.patch(f"{A}/users/{worker_admin.id}", json={"is_active": False}).status_code == 200
    assert worker.get(f"{A}/auth/me").status_code == 401
    fresh = make_client()
    assert (
        fresh.post(
            f"{A}/auth/login", json={"email": worker_admin.email, "password": PASSWORD}
        ).status_code
        == 401
    )

    boss.patch(
        f"{A}/users/{worker_admin.id}", json={"is_active": True, "password": "a-brand-new-password"}
    )
    assert (
        fresh.post(
            f"{A}/auth/login", json={"email": worker_admin.email, "password": PASSWORD}
        ).status_code
        == 401
    )
    assert (
        fresh.post(
            f"{A}/auth/login",
            json={"email": worker_admin.email, "password": "a-brand-new-password"},
        ).status_code
        == 200
    )


def test_update_unknown_admin_and_null_fields(login_as):
    boss, _ = login_as(SUPER)
    assert boss.patch(f"{A}/users/{ID}", json={"full_name": "x"}).status_code == 404
    assert boss.patch(f"{A}/users/{ID}", json={"role": None}).status_code == 422
