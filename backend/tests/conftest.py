import os
from pathlib import Path

os.environ.setdefault("JWT_SECRET", "test-only-secret-" + "x" * 32)  # before the app reads settings

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture(scope="session")
def pg_engine():
    """Fresh schema built by the real Alembic migration. Needs TEST_DATABASE_URL (PostgreSQL)."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set; skipping PostgreSQL tests")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL  # alembic/env.py reads settings
    from app.core.config import get_settings

    get_settings.cache_clear()
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    command.upgrade(alembic_config(TEST_DATABASE_URL), "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db(pg_engine):
    """Each test runs in a transaction that is rolled back."""
    conn = pg_engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    trans.rollback()
    conn.close()


ORIGIN = "http://localhost:3000"  # an allowed CORS origin; browsers send it on unsafe requests


@pytest.fixture(autouse=True)
def _rate_limits_off():
    """Rate limiting is enabled explicitly in the tests that exercise it."""
    from app.core.ratelimit import limiter

    limiter.enabled = False
    limiter.reset()
    yield
    limiter.enabled = False


@pytest.fixture
def make_client(db):
    """Factory for independent API clients (each with its own cookie jar) sharing the test transaction."""
    from fastapi.testclient import TestClient

    from app.core.db import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db

    def factory(origin: str | None = ORIGIN) -> TestClient:
        return TestClient(app, headers={"Origin": origin} if origin else {})

    yield factory
    app.dependency_overrides.clear()


@pytest.fixture
def client(make_client):
    """Anonymous API client."""
    return make_client()


PASSWORD = "correct-horse-battery"
_counter = iter(range(1, 10_000))


@pytest.fixture
def make_admin(db):
    from app.models.enums import AdminRole
    from app.schemas.auth import AdminCreate
    from app.services import admins

    def factory(
        role: AdminRole = AdminRole.MANAGER, email: str | None = None, password: str = PASSWORD
    ):
        email = email or f"admin{next(_counter)}@example.com"
        return admins.create_admin(db, AdminCreate(email=email, password=password, role=role))

    return factory


@pytest.fixture
def login_as(make_client, make_admin):
    """login_as(role) -> (client logged in as a fresh admin of that role, admin)."""
    from app.models.enums import AdminRole

    def factory(role: AdminRole = AdminRole.MANAGER):
        admin = make_admin(role)
        c = make_client()
        r = c.post("/api/v1/admin/auth/login", json={"email": admin.email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return c, admin

    return factory
