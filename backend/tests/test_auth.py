import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.core.config import Settings, get_settings
from app.core.ratelimit import limiter
from app.models import AdminSession
from app.models.enums import AdminRole
from tests.conftest import ORIGIN, PASSWORD

AUTH = "/api/v1/admin/auth"
ME = f"{AUTH}/me"
GENERIC = "Invalid email or password."


def login(client, email, password=PASSWORD):
    return client.post(f"{AUTH}/login", json={"email": email, "password": password})


# ---------------- passwords ----------------
def test_passwords_are_hashed_with_argon2(make_admin):
    admin = make_admin()
    assert admin.password_hash.startswith("$argon2id$") and PASSWORD not in admin.password_hash
    assert security.verify_password(PASSWORD, admin.password_hash)
    assert not security.verify_password("wrong", admin.password_hash)
    assert not security.verify_password(PASSWORD, None)  # unknown user path never succeeds


# ---------------- login ----------------
def test_login_sets_httponly_cookies_and_returns_profile(client, make_admin):
    admin = make_admin(AdminRole.STAFF, email="Staff@Example.com")  # stored lower-case
    r = login(client, "STAFF@example.com")  # case-insensitive
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "staff@example.com" and body["role"] == "staff"
    assert "password" not in str(body) and body["last_login_at"] is not None
    assert "access_token" not in body  # tokens are never exposed to JavaScript
    cookies = r.headers.get_list("set-cookie")
    assert len(cookies) == 2
    for c in cookies:
        assert "HttpOnly" in c and "SameSite=lax" in c
    access = next(c for c in cookies if c.startswith("gg_access="))
    refresh = next(c for c in cookies if c.startswith("gg_refresh="))
    assert (
        "Path=/api/v1;" in access + ";" and "Path=/api/v1/admin/auth" in refresh
    )  # refresh is path-scoped
    assert client.get(ME).json()["id"] == str(admin.id)


def test_login_failures_are_indistinguishable(client, make_admin, db):
    ok = make_admin(email="a@example.com")
    inactive = make_admin(email="off@example.com")
    inactive.is_active = False
    db.flush()
    attempts = [
        ("a@example.com", "wrong-password"),
        ("nobody@example.com", PASSWORD),
        ("off@example.com", PASSWORD),
    ]
    for email, pw in attempts:
        r = login(client, email, pw)
        assert r.status_code == 401 and r.json() == {"detail": GENERIC}
        assert "set-cookie" not in r.headers
    assert ok.last_login_at is None


def test_login_input_validation(client):
    assert (
        client.post(f"{AUTH}/login", json={"email": "not-an-email", "password": "x"}).status_code
        == 422
    )
    assert client.post(f"{AUTH}/login", json={"email": "a@b.co"}).status_code == 422
    assert (
        client.post(f"{AUTH}/login", json={"email": "a@b.co", "password": "x" * 1000}).status_code
        == 422
    )


def test_login_is_rate_limited(client, make_admin):
    admin = make_admin()
    limiter.enabled = True
    limiter.reset()
    codes = [login(client, admin.email, "wrong").status_code for _ in range(7)]
    assert codes[:5] == [401] * 5 and codes[5] == 429
    assert (
        client.post(f"{AUTH}/login", json={"email": admin.email, "password": PASSWORD}).status_code
        == 429
    )


# ---------------- access token validation ----------------
def test_unauthenticated_and_garbage_tokens_rejected(client):
    assert client.get(ME).status_code == 401
    client.cookies.set("gg_access", "not-a-jwt", path="/api/v1")
    assert client.get(ME).status_code == 401


def forge(claims_overrides=None, secret=None, algorithm="HS256", typ="access", sid=None, sub=None):
    now = datetime.now(UTC)
    claims = {
        "iss": security.ISSUER, "aud": security.AUDIENCE, "typ": typ, "jti": uuid.uuid4().hex,
        "sub": str(sub or uuid.uuid4()), "sid": str(sid or uuid.uuid4()),
        "iat": now, "exp": now + timedelta(minutes=5),
    }  # fmt: skip
    claims.update(claims_overrides or {})
    return jwt.encode(claims, secret or get_settings().jwt_secret, algorithm=algorithm)


def test_forged_tokens_rejected(client, login_as, db):
    _, admin = login_as()
    session = db.query(AdminSession).filter_by(admin_id=admin.id).one()
    valid = {"sid": session.id, "sub": admin.id}
    cases = {
        "wrong secret": forge(secret="x" * 40, **valid),
        "expired": forge({"exp": datetime.now(UTC) - timedelta(seconds=5)}, **valid),
        "wrong audience": forge({"aud": "someone-else"}, **valid),
        "wrong issuer": forge({"iss": "evil"}, **valid),
        "refresh token used as access": forge(typ="refresh", **valid),
        "missing claims": jwt.encode(
            {"sub": str(admin.id)}, get_settings().jwt_secret, algorithm="HS256"
        ),
        "alg none": jwt.encode(
            {"sub": str(admin.id), "sid": str(session.id)}, None, algorithm="none"
        ),
        "unknown session": forge(sub=admin.id),
        "session of another admin": forge(sid=session.id),
    }
    for name, token in cases.items():
        c = TestClient(client.app, headers={"Origin": ORIGIN})
        c.cookies.set("gg_access", token, path="/api/v1")
        assert c.get(ME).status_code == 401, name
    # sanity: the same helper produces a token the API accepts
    c = TestClient(client.app, headers={"Origin": ORIGIN})
    c.cookies.set("gg_access", forge(**valid), path="/api/v1")
    assert c.get(ME).status_code == 200


def test_expired_access_token_is_rejected(client, make_admin, monkeypatch):
    admin = make_admin()
    monkeypatch.setattr(get_settings(), "access_token_minutes", -1)
    assert login(client, admin.email).status_code == 200
    assert client.get(ME).status_code == 401


def test_deactivated_admin_loses_access_immediately(client, login_as, db):
    c, admin = login_as()
    assert c.get(ME).status_code == 200
    admin.is_active = False
    db.flush()
    assert c.get(ME).status_code == 401


def test_role_change_applies_immediately(login_as, db):
    c, admin = login_as(AdminRole.STAFF)
    assert c.post("/api/v1/admin/categories", json={"name": "X"}).status_code == 403
    admin.role = AdminRole.MANAGER
    db.flush()
    assert c.post("/api/v1/admin/categories", json={"name": "X"}).status_code == 201


# ---------------- refresh ----------------
def test_refresh_rotates_tokens(client, make_admin, db):
    admin = make_admin()
    login(client, admin.email)
    session = db.query(AdminSession).filter_by(admin_id=admin.id).one()
    first_hash = session.refresh_jti_hash
    assert len(first_hash) == 64
    r = client.post(f"{AUTH}/refresh")
    assert r.status_code == 200 and r.json()["email"] == admin.email
    assert len(r.headers.get_list("set-cookie")) == 2
    db.refresh(session)
    assert session.refresh_jti_hash != first_hash
    assert client.get(ME).status_code == 200


def test_refresh_token_reuse_revokes_the_session(client, make_admin, db):
    admin = make_admin()
    login(client, admin.email)
    stolen = client.cookies.get("gg_refresh", path="/api/v1/admin/auth")
    assert client.post(f"{AUTH}/refresh").status_code == 200  # legitimate rotation

    attacker = TestClient(client.app, headers={"Origin": ORIGIN})
    attacker.cookies.set("gg_refresh", stolen, path="/api/v1/admin/auth")
    assert attacker.post(f"{AUTH}/refresh").status_code == 401  # replay of the old token
    # ...and the legitimate session is now ended too
    assert client.get(ME).status_code == 401
    assert client.post(f"{AUTH}/refresh").status_code == 401


def test_refresh_rejects_missing_wrong_type_and_garbage(client, login_as):
    assert client.post(f"{AUTH}/refresh").status_code == 401
    c, _ = login_as()
    access = c.cookies.get("gg_access", path="/api/v1")
    bad = TestClient(client.app, headers={"Origin": ORIGIN})
    bad.cookies.set("gg_refresh", access, path="/api/v1/admin/auth")  # access token as refresh
    assert bad.post(f"{AUTH}/refresh").status_code == 401
    bad.cookies.set("gg_refresh", "junk", path="/api/v1/admin/auth")
    assert bad.post(f"{AUTH}/refresh").status_code == 401


def test_refresh_fails_for_expired_or_too_old_sessions(client, make_admin, db):
    admin = make_admin()
    login(client, admin.email)
    session = db.query(AdminSession).filter_by(admin_id=admin.id).one()
    session.created_at = datetime.now(UTC) - timedelta(days=get_settings().session_max_days + 1)
    db.flush()
    assert client.post(f"{AUTH}/refresh").status_code == 401  # absolute lifetime exceeded

    session.created_at = datetime.now(UTC)
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.flush()
    assert client.post(f"{AUTH}/refresh").status_code == 401  # sliding expiry passed


# ---------------- logout ----------------
def test_logout_revokes_session_and_clears_cookies(client, make_admin, db):
    admin = make_admin()
    login(client, admin.email)
    old_access = client.cookies.get("gg_access", path="/api/v1")
    r = client.post(f"{AUTH}/logout")
    assert r.status_code == 204
    cleared = r.headers.get_list("set-cookie")
    assert len(cleared) == 2 and all("Max-Age=0" in c for c in cleared)
    assert db.query(AdminSession).filter_by(admin_id=admin.id).one().revoked_at is not None

    # a copied access token no longer works even though it has not expired
    replay = TestClient(client.app, headers={"Origin": ORIGIN})
    replay.cookies.set("gg_access", old_access, path="/api/v1")
    assert replay.get(ME).status_code == 401
    assert client.post(f"{AUTH}/refresh").status_code == 401


def test_logout_is_idempotent_and_works_without_cookies(client):
    assert client.post(f"{AUTH}/logout").status_code == 204


def test_logout_works_when_access_token_expired(client, make_admin, db, monkeypatch):
    admin = make_admin()
    monkeypatch.setattr(get_settings(), "access_token_minutes", -1)
    login(client, admin.email)
    assert client.post(f"{AUTH}/logout").status_code == 204
    assert db.query(AdminSession).filter_by(admin_id=admin.id).one().revoked_at is not None


def test_logout_only_ends_the_current_session(make_client, make_admin):
    admin = make_admin()
    laptop, phone = make_client(), make_client()
    login(laptop, admin.email)
    login(phone, admin.email)
    laptop.post(f"{AUTH}/logout")
    assert laptop.get(ME).status_code == 401
    assert phone.get(ME).status_code == 200


# ---------------- CSRF ----------------
def test_state_changing_requests_need_an_allowed_origin(client, make_client, make_admin):
    admin = make_admin()
    login(client, admin.email)
    evil = {"Origin": "https://evil.example"}
    assert (
        client.post("/api/v1/admin/categories", json={"name": "X"}, headers=evil).status_code == 403
    )
    assert client.post(f"{AUTH}/logout", headers=evil).status_code == 403
    assert client.post(f"{AUTH}/refresh", headers=evil).status_code == 403
    assert login(client, admin.email).status_code == 200  # still allowed from the real origin

    no_origin = make_client(origin=None)
    no_origin.cookies.update(client.cookies)
    assert no_origin.post("/api/v1/admin/categories", json={"name": "X"}).status_code == 403
    assert no_origin.get(ME).status_code == 200  # safe methods are not origin-checked

    assert (
        make_client(origin="https://evil.example")
        .post(f"{AUTH}/login", json={"email": admin.email, "password": PASSWORD})
        .status_code
        == 403
    )


# ---------------- configuration ----------------
def test_insecure_production_config_refuses_to_start():
    good = {
        "app_env": "production",
        "jwt_secret": "s" * 40,
        "cookie_secure": True,
        "storage_backend": "supabase",
    }
    Settings(**good).validate_for_runtime()
    for override in (
        {"jwt_secret": "short"},
        {"cookie_secure": False},
        {"cors_origins": ["*"]},
        {"storage_backend": "local"},
    ):
        with pytest.raises(RuntimeError):
            Settings(**{**good, **override}).validate_for_runtime()
    Settings(app_env="development", jwt_secret="").validate_for_runtime()  # dev is lenient


def test_missing_jwt_secret_fails_closed(client, make_admin, monkeypatch):
    admin = make_admin()
    monkeypatch.setattr(get_settings(), "jwt_secret", "")
    assert login(client, admin.email).status_code == 503
