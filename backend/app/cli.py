"""Admin bootstrap commands. Usage (from backend/):

    uv run python -m app.cli create-admin EMAIL [--role super_admin|manager|staff] [--name NAME]
    uv run python -m app.cli set-password EMAIL

The password is always prompted (never passed as an argument) so it stays out of shell history.
"""

import argparse
import getpass
import sys

from pydantic import ValidationError

from app.core.db import get_session_factory
from app.core.errors import AppError
from app.models.enums import AdminRole
from app.repositories import admins as repo
from app.schemas.auth import AdminCreate, AdminUpdate
from app.services import admins as service


def _prompt_password() -> str:
    first = getpass.getpass("Password: ")
    if first != getpass.getpass("Repeat password: "):
        sys.exit("Passwords do not match.")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-admin")
    create.add_argument("email")
    create.add_argument(
        "--role", choices=[r.value for r in AdminRole], default=AdminRole.SUPER_ADMIN.value
    )
    create.add_argument("--name")
    reset = sub.add_parser("set-password")
    reset.add_argument("email")
    args = parser.parse_args(argv)

    try:
        with get_session_factory()() as db:
            if args.command == "create-admin":
                admin = service.create_admin(
                    db,
                    AdminCreate(
                        email=args.email,
                        password=_prompt_password(),
                        full_name=args.name,
                        role=AdminRole(args.role),
                    ),
                )
                print(f"Created {admin.role.value} {admin.email}")
            else:
                admin = repo.get_by_email(db, args.email.strip().lower())
                if admin is None:
                    sys.exit("No such admin.")
                service.update_admin(
                    db, actor=None, admin_id=admin.id, data=AdminUpdate(password=_prompt_password())
                )
                print(f"Password updated for {admin.email}; all sessions revoked.")
    except (AppError, ValidationError) as exc:
        sys.exit(str(getattr(exc, "message", exc)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
