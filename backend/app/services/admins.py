import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import Admin
from app.repositories import admins as repo
from app.schemas.auth import AdminCreate, AdminUpdate


def list_admins(db: Session) -> list[Admin]:
    return repo.list_all(db)


def create_admin(db: Session, data: AdminCreate) -> Admin:
    if repo.get_by_email(db, data.email):
        raise ConflictError("An admin with this email already exists.")
    admin = Admin(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(admin)
    db.commit()
    return admin


def update_admin(db: Session, actor: Admin | None, admin_id: uuid.UUID, data: AdminUpdate) -> Admin:
    admin = repo.get(db, admin_id)
    if admin is None:
        raise NotFoundError("Admin not found.")
    changes = data.model_dump(exclude_unset=True)

    if actor is not None and admin.id == actor.id and ("role" in changes or "is_active" in changes):
        # Also guarantees the last active super_admin can never be demoted or disabled.
        raise BusinessRuleError("You cannot change your own role or active status.")

    password = changes.pop("password", None)
    for field, value in changes.items():
        setattr(admin, field, value)
    if password is not None:
        admin.password_hash = hash_password(password)
    if password is not None or changes.get("is_active") is False:
        repo.revoke_admin_sessions(db, admin.id, datetime.now(UTC))  # force re-login everywhere
    db.commit()
    return admin
