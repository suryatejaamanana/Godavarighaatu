import hashlib
import hmac
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError, UnauthorizedError

ISSUER = "godavarighaatu-api"
AUDIENCE = "godavarighaatu-admin"
ALGORITHM = "HS256"  # fixed: never read from the token header

TokenType = Literal["access", "refresh"]

_hasher = PasswordHasher()
# Verified against when the email is unknown, so login timing doesn't reveal which emails exist.
_DUMMY_HASH = _hasher.hash("not-a-real-password")

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()


def digests_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


@dataclass(frozen=True)
class TokenClaims:
    admin_id: uuid.UUID
    session_id: uuid.UUID
    jti: str
    type: TokenType


def _secret() -> str:
    secret = get_settings().jwt_secret
    if not secret:
        raise ServiceUnavailableError("Authentication is not configured (JWT_SECRET).")
    return secret


def _encode(admin_id: uuid.UUID, session_id: uuid.UUID, typ: TokenType, ttl: timedelta, **extra):
    now = datetime.now(UTC)
    jti = uuid.uuid4().hex
    payload = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": str(admin_id),
        "sid": str(session_id),
        "typ": typ,
        "jti": jti,
        "iat": now,
        "exp": now + ttl,
        **extra,
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM), jti, payload["exp"]


def create_access_token(admin_id: uuid.UUID, session_id: uuid.UUID) -> str:
    ttl = timedelta(minutes=get_settings().access_token_minutes)
    return _encode(admin_id, session_id, "access", ttl)[0]


def create_refresh_token(admin_id: uuid.UUID, session_id: uuid.UUID) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at)."""
    ttl = timedelta(days=get_settings().refresh_token_days)
    return _encode(admin_id, session_id, "refresh", ttl)


def decode_token(token: str, expected: TokenType, *, verify_exp: bool = True) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": ["exp", "iat", "sub", "sid", "typ", "jti"],
                "verify_exp": verify_exp,
            },
        )
        if payload["typ"] != expected:
            raise jwt.InvalidTokenError("wrong token type")
        return TokenClaims(
            admin_id=uuid.UUID(payload["sub"]),
            session_id=uuid.UUID(payload["sid"]),
            jti=payload["jti"],
            type=expected,
        )
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc
