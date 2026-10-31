import os
from pathlib import Path

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


@pytest.fixture
def client(db):
    """API client whose requests share the rolled-back test transaction."""
    from fastapi.testclient import TestClient

    from app.core.db import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
