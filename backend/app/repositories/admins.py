import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models import Admin, AdminSession


def get(db: Session, admin_id: uuid.UUID) -> Admin | None:
    return db.get(Admin, admin_id)


def get_by_email(db: Session, email: str) -> Admin | None:
    return db.scalar(select(Admin).where(Admin.email == email))


def list_all(db: Session) -> list[Admin]:
    return list(db.scalars(select(Admin).order_by(Admin.created_at)))


def get_session(
    db: Session, session_id: uuid.UUID, *, for_update: bool = False
) -> AdminSession | None:
    stmt = (
        select(AdminSession)
        .where(AdminSession.id == session_id)
        .options(joinedload(AdminSession.admin))
    )
    if for_update:
        stmt = stmt.with_for_update(of=AdminSession)
    return db.scalar(stmt)


def revoke_admin_sessions(db: Session, admin_id: uuid.UUID, now: datetime) -> None:
    db.execute(
        update(AdminSession)
        .where(AdminSession.admin_id == admin_id, AdminSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
