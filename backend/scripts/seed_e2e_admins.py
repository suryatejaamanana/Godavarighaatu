"""Development/test only: create a manager and a staff admin for the browser (Playwright) tests.

    DATABASE_URL=... JWT_SECRET=... uv run python -m scripts.seed_e2e_admins

Idempotent. Never run against a production database.
"""

import sys

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models.enums import AdminRole
from app.repositories import admins as repo
from app.schemas.auth import AdminCreate
from app.services import admins

PASSWORD = "e2e-test-password-1"
USERS = [("e2e-manager@example.com", AdminRole.MANAGER), ("e2e-staff@example.com", AdminRole.STAFF)]

if not get_settings().is_development:
    sys.exit("Refusing to seed test admins outside APP_ENV=development.")

with get_session_factory()() as db:
    for email, role in USERS:
        if repo.get_by_email(db, email) is None:
            admins.create_admin(db, AdminCreate(email=email, password=PASSWORD, role=role))
            print(f"created {email} ({role.value})")
        else:
            print(f"exists  {email}")
