import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    digests_equal,
    hash_jti,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.models import Admin, AdminSession
from app.repositories import admins as repo

INVALID_CREDENTIALS = "Invalid email or password."


def _now() -> datetime:
    return datetime.now(UTC)


def _session_usable(session: AdminSession | None, now: datetime) -> bool:
    if session is None or session.revoked_at is not None or not session.admin.is_active:
        return False
    absolute_limit = session.created_at + timedelta(days=get_settings().session_max_days)
    return session.expires_at > now and absolute_limit > now


def login(db: Session, email: str, password: str, user_agent: str | None) -> tuple[Admin, str, str]:
    """Returns (admin, access_token, refresh_token). The same error is used for every failure."""
    admin = repo.get_by_email(db, email)
    password_ok = verify_password(password, admin.password_hash if admin else None)
    if admin is None or not password_ok or not admin.is_active:
        raise UnauthorizedError(INVALID_CREDENTIALS)

    if password_needs_rehash(admin.password_hash):
        admin.password_hash = hash_password(password)

    now = _now()
    session = AdminSession(
        admin_id=admin.id,
        expires_at=now,  # replaced below once the refresh token (and its expiry) exists
        user_agent=(user_agent or "")[:255] or None,
    )
    db.add(session)
    db.flush()
    refresh, jti, expires_at = create_refresh_token(admin.id, session.id)
    session.refresh_jti_hash = hash_jti(jti)
    session.expires_at = expires_at
    session.last_used_at = now
    admin.last_login_at = now
    db.commit()
    return admin, create_access_token(admin.id, session.id), refresh


def refresh(db: Session, refresh_token: str) -> tuple[Admin, str, str]:
    """Rotate the refresh token. Replaying an already-used token revokes the whole session."""
    claims = decode_token(refresh_token, "refresh")
    now = _now()
    session = repo.get_session(db, claims.session_id, for_update=True)
    if not _session_usable(session, now) or session.admin_id != claims.admin_id:
        raise UnauthorizedError("Invalid or expired token.")

    if not digests_equal(session.refresh_jti_hash, hash_jti(claims.jti)):
        session.revoked_at = now  # token reuse: assume theft, end the session
        db.commit()
        raise UnauthorizedError("Invalid or expired token.")

    new_refresh, jti, expires_at = create_refresh_token(session.admin_id, session.id)
    session.refresh_jti_hash = hash_jti(jti)
    session.expires_at = expires_at
    session.last_used_at = now
    db.commit()
    return session.admin, create_access_token(session.admin_id, session.id), new_refresh


def authenticate_access_token(db: Session, access_token: str) -> Admin:
    """Valid signature + not expired + session not revoked + admin still active."""
    claims = decode_token(access_token, "access")
    session = repo.get_session(db, claims.session_id)
    if not _session_usable(session, _now()) or session.admin_id != claims.admin_id:
        raise UnauthorizedError("Invalid or expired token.")
    return session.admin  # role comes from the database, so role changes apply immediately


def logout(db: Session, *, refresh_token: str | None, access_token: str | None) -> None:
    """Idempotent. Works even if the access token has already expired."""
    session_id: uuid.UUID | None = None
    for token, kind in ((refresh_token, "refresh"), (access_token, "access")):
        if not token:
            continue
        try:
            session_id = decode_token(token, kind, verify_exp=False).session_id
            break
        except UnauthorizedError:
            continue
    if session_id is None:
        return
    session = repo.get_session(db, session_id)
    if session and session.revoked_at is None:
        session.revoked_at = _now()
        db.commit()
