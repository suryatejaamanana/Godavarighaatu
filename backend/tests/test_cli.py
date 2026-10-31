from contextlib import contextmanager

import pytest

from app import cli
from app.core.security import verify_password
from app.models.enums import AdminRole
from app.repositories import admins as repo
from tests.conftest import PASSWORD


@pytest.fixture
def cli_env(db, monkeypatch):
    @contextmanager
    def session():
        yield db  # share the test transaction; don't close it

    monkeypatch.setattr(cli, "get_session_factory", lambda: session)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt="": PASSWORD)


def test_create_admin_and_set_password(cli_env, db, make_client):
    assert cli.main(["create-admin", "Owner@Example.com", "--name", "Owner"]) == 0
    admin = repo.get_by_email(db, "owner@example.com")
    assert admin.role == AdminRole.SUPER_ADMIN and verify_password(PASSWORD, admin.password_hash)
    assert (
        make_client()
        .post("/api/v1/admin/auth/login", json={"email": "owner@example.com", "password": PASSWORD})
        .status_code
        == 200
    )

    cli.getpass.getpass = lambda prompt="": "another-long-password"
    assert cli.main(["set-password", "owner@example.com"]) == 0
    db.refresh(admin)
    assert verify_password("another-long-password", admin.password_hash)


def test_cli_rejects_bad_input(cli_env, monkeypatch):
    with pytest.raises(SystemExit):
        cli.main(["create-admin", "dup@example.com"])
        cli.main(["create-admin", "dup@example.com"])  # duplicate email
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt="": "short")
    with pytest.raises(SystemExit):
        cli.main(["create-admin", "weak@example.com"])  # password policy
    with pytest.raises(SystemExit):
        cli.main(["set-password", "nobody@example.com"])
