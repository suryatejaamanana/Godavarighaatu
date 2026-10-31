from fastapi import APIRouter, Request, Response, status

from app.api.deps import ACCESS_COOKIE, REFRESH_COOKIE, CurrentAdmin, check_csrf
from app.core.config import get_settings
from app.core.db import DB
from app.core.errors import UnauthorizedError
from app.core.ratelimit import limiter
from app.schemas.auth import AdminOut, LoginRequest
from app.services import auth as service

router = APIRouter(prefix="/auth", tags=["admin: auth"])

_settings = get_settings()
# The refresh cookie is only sent to the auth endpoints; the access cookie to the whole API.
API_PATH = "/api/v1"
AUTH_PATH = "/api/v1/admin/auth"


def _set_cookies(response: Response, access: str, refresh: str) -> None:
    s = get_settings()
    common = {
        "httponly": True,
        "secure": s.cookie_secure,
        "samesite": s.cookie_samesite,
        "domain": s.cookie_domain,
    }
    response.set_cookie(
        ACCESS_COOKIE, access, max_age=s.access_token_minutes * 60, path=API_PATH, **common
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh, max_age=s.refresh_token_days * 86400, path=AUTH_PATH, **common
    )


def _clear_cookies(response: Response) -> None:
    s = get_settings()
    for name, path in ((ACCESS_COOKIE, API_PATH), (REFRESH_COOKIE, AUTH_PATH)):
        response.delete_cookie(name, path=path, domain=s.cookie_domain)


@router.post("/login", response_model=AdminOut)
@limiter.limit(_settings.login_rate_limit)
def login(request: Request, response: Response, data: LoginRequest, db: DB):
    check_csrf(request)
    admin, access, refresh = service.login(
        db, data.email, data.password, request.headers.get("user-agent")
    )
    _set_cookies(response, access, refresh)
    return admin


@router.post("/refresh", response_model=AdminOut)
@limiter.limit(_settings.refresh_rate_limit)
def refresh(request: Request, response: Response, db: DB):
    check_csrf(request)
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise UnauthorizedError("Not authenticated.")
    admin, access, new_refresh = service.refresh(db, token)
    _set_cookies(response, access, new_refresh)
    return admin


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: DB):
    check_csrf(request)
    service.logout(
        db,
        refresh_token=request.cookies.get(REFRESH_COOKIE),
        access_token=request.cookies.get(ACCESS_COOKIE),
    )
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_cookies(response)
    return response


@router.get("/me", response_model=AdminOut)
def me(admin: CurrentAdmin):
    return admin
